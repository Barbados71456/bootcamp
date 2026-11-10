import json
import os
import secrets
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from flask import Flask, g, jsonify, render_template, request, session
from werkzeug.exceptions import HTTPException
from content import COURSES, ACHIEVEMENTS

app = Flask(__name__)
root = Path(os.environ.get('STUDYFLOW_DATA_DIR', Path(__file__).parent / 'instance'))
root.mkdir(parents=True, exist_ok=True)
key_path = root / 'secret.key'
if not os.environ.get('SECRET_KEY') and not key_path.exists():
    try:
        with key_path.open('x') as f:
            f.write(secrets.token_hex(32))
    except FileExistsError:
        pass
app.secret_key = os.environ.get('SECRET_KEY') or key_path.read_text()
app.config.update(DATABASE=str(root / 'studyflow.sqlite3'), SESSION_COOKIE_HTTPONLY=True,
                  SESSION_COOKIE_SAMESITE='Lax', MAX_CONTENT_LENGTH=64 * 1024,
                  PERMANENT_SESSION_LIFETIME=timedelta(days=365))

def today():
    return datetime.now(timezone(timedelta(hours=3))).date()

def new_user():
    return {'pet': {'name': 'Кодик', 'level': 1, 'xp': 0, 'hunger': 50, 'happiness': 80},
            'kanban': {'todo': [], 'doing': [], 'done': []},
            'stats': {'total_minutes': 0, 'pomodoros': 0, 'lessons_done': 0},
            'lessons': {}, 'daily_goal': 30, 'activity': {}, 'timer_ids': [], 'unlocked': []}

@app.before_request
def load_user():
    if request.endpoint == 'static':
        return
    if request.method == 'POST':
        if request.headers.get('Sec-Fetch-Site') == 'cross-site':
            return jsonify(ok=False, error='Запрос с другого сайта запрещён'), 403
        if not request.is_json:
            return jsonify(ok=False, error='Ожидается JSON'), 415
        if not isinstance(request.get_json(), dict):
            return jsonify(ok=False, error='Ожидается объект JSON'), 400
    session.permanent = True
    session.setdefault('uid', str(uuid.uuid4()))
    g.db = sqlite3.connect(app.config['DATABASE'], timeout=15)
    g.db.execute('CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, data TEXT NOT NULL)')
    # Serialize read-modify-write across workers so simultaneous requests cannot lose progress.
    g.db.execute('BEGIN IMMEDIATE')
    row = g.db.execute('SELECT data FROM users WHERE id=?', (session['uid'],)).fetchone()
    g.user = json.loads(row[0]) if row else new_user()

@app.after_request
def save_user(response):
    if hasattr(g, 'user') and response.status_code < 400:
        for achievement in ACHIEVEMENTS:
            if achievement['check'](g.user) and achievement['id'] not in g.user['unlocked']:
                g.user['unlocked'].append(achievement['id'])
        g.db.execute('INSERT OR REPLACE INTO users VALUES (?, ?)',
                     (session['uid'], json.dumps(g.user, ensure_ascii=False)))
        g.db.commit()
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    if request.endpoint != 'static':
        response.headers['Cache-Control'] = 'no-store'
    return response

@app.teardown_request
def close_db(error):
    if hasattr(g, 'db'):
        g.db.close()

@app.errorhandler(HTTPException)
def http_error(error):
    if request.path.startswith('/api/'):
        return jsonify(ok=False, error=error.description), error.code
    return error

@app.errorhandler(ValueError)
def invalid_value(error):
    return jsonify(ok=False, error=str(error)), 400

def data():
    return request.get_json()

def text(value, limit, required=False):
    if not isinstance(value, str) or len(value) > limit or (required and not value.strip()):
        raise ValueError(f'Введите текст длиной от {1 if required else 0} до {limit} символов')
    return value.strip()

def integer(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'Введите целое число от {low} до {high}')
    return value

def award(amount):
    pet = g.user['pet']
    level, pet['xp'] = divmod(pet['xp'] + amount, 100)
    pet['level'] += level
    pet['happiness'] = min(100, pet['happiness'] + level * 10)

def activity(minutes):
    key = today().isoformat()
    g.user['activity'][key] = g.user['activity'].get(key, 0) + minutes
    g.user['stats']['total_minutes'] += minutes

def items():
    return [{k: v for k, v in a.items() if k != 'check'} |
            {'unlocked': a['id'] in g.user['unlocked'] or bool(a['check'](g.user))} for a in ACHIEVEMENTS]

def summary():
    day = today()
    streak = 0
    cursor = day if g.user['activity'].get(day.isoformat()) else day - timedelta(days=1)
    while g.user['activity'].get(cursor.isoformat(), 0):
        streak += 1
        cursor -= timedelta(days=1)
    week = [{'date': (day - timedelta(days=i)).isoformat(),
             'minutes': g.user['activity'].get((day - timedelta(days=i)).isoformat(), 0)} for i in range(6, -1, -1)]
    return dict(streak=streak, week=week, today=g.user['activity'].get(day.isoformat(), 0))

@app.route('/')
def index():
    next_lesson = next(((c, l) for c in COURSES for l in c['lessons']
                        if not g.user['lessons'].get(f"{c['id']}:{l['id']}", {}).get('completed')), None)
    return render_template('index.html', user=g.user, courses=COURSES,
                           total_lessons=sum(len(c['lessons']) for c in COURSES),
                           summary=summary(), next_lesson=next_lesson)

@app.route('/<page>')
def page(page):
    if page not in ('courses', 'kanban', 'timer', 'pet', 'achievements', 'insights'):
        from flask import abort
        abort(404)
    achievements = items()
    return render_template(page + '.html', user=g.user, courses=COURSES, summary=summary(),
                           achievements=achievements, unlocked_count=sum(a['unlocked'] for a in achievements),
                           total_count=len(achievements))

@app.get('/api/kanban')
def kanban_get():
    return jsonify(g.user['kanban'])

def task_fields(d):
    title = text(d.get('title'), 120, True)
    priority = d.get('priority', 'normal')
    if priority not in ('low', 'normal', 'high'):
        raise ValueError('Неизвестный приоритет')
    due = text(d.get('due', ''), 10)
    if due:
        try:
            datetime.strptime(due, '%Y-%m-%d')
        except ValueError:
            raise ValueError('Неверная дата срока')
    return dict(title=title, priority=priority, due=due)

@app.post('/api/kanban/add')
def kanban_add():
    d = data()
    col = d.get('column', 'todo')
    if not isinstance(col, str) or col not in g.user['kanban']:
        raise ValueError('Неверная колонка')
    card = task_fields(d) | {'id': str(uuid.uuid4()), 'rewarded': col == 'done'}
    g.user['kanban'][col].append(card)
    award(10 if col == 'done' else 2)
    return jsonify(ok=True, card=card, pet=g.user['pet'])

@app.post('/api/kanban/<action>')
def kanban_change(action):
    d = data()
    found = next(((col, card) for col, cards in g.user['kanban'].items() for card in cards if card['id'] == d.get('id')), None)
    if not found:
        return jsonify(ok=False, error='Карточка не найдена'), 404
    col, card = found
    if action == 'edit':
        card.update(task_fields(d))
    elif action == 'delete':
        g.user['kanban'][col].remove(card)
    elif action == 'move':
        target = d.get('to')
        if not isinstance(target, str) or target not in g.user['kanban']:
            raise ValueError('Неверная колонка')
        g.user['kanban'][col].remove(card)
        g.user['kanban'][target].append(card)
        if target == 'done' and not card.get('rewarded'):
            award(10)
            card['rewarded'] = True
    else:
        return jsonify(ok=False, error='Неизвестное действие'), 404
    return jsonify(ok=True, pet=g.user['pet'])

def lesson(d):
    course = next((c for c in COURSES if c['id'] == d.get('course')), None)
    entry = next((l for l in course['lessons'] if l['id'] == d.get('lesson')), None) if course else None
    if entry is None:
        raise ValueError('Урок не найден')
    key = f"{course['id']}:{entry['id']}"
    return entry, g.user['lessons'].setdefault(key, {'completed': False, 'note': '', 'bookmark': False})

@app.post('/api/lesson/<action>')
def lesson_change(action):
    entry, state = lesson(data())
    if action == 'complete':
        if not state['completed']:
            state['completed'] = True
            g.user['stats']['lessons_done'] += 1
            activity(entry['minutes'])
            award(entry['minutes'])
    elif action == 'note':
        state['note'] = text(data().get('note'), 5000)
    elif action == 'bookmark':
        if type(data().get('bookmark')) is not bool:
            raise ValueError('Ожидается логическое значение')
        state['bookmark'] = data()['bookmark']
    else:
        return jsonify(ok=False, error='Неизвестное действие'), 404
    return jsonify(ok=True, state=state, stats=g.user['stats'], pet=g.user['pet'])

@app.post('/api/timer/finish')
def timer_finish():
    minutes = integer(data().get('minutes'), 1, 120)
    token = text(data().get('id'), 80, True)
    if token not in g.user['timer_ids']:
        g.user['timer_ids'].append(token)
        activity(minutes)
        g.user['stats']['pomodoros'] += 1
        award(minutes // 5)
    return jsonify(ok=True, stats=g.user['stats'], pet=g.user['pet'])

@app.post('/api/pet/<action>')
def pet_change(action):
    pet = g.user['pet']
    if action == 'rename':
        pet['name'] = text(data().get('name'), 20, True)
    elif action == 'feed':
        pet['hunger'] = min(100, pet['hunger'] + 25)
        pet['happiness'] = min(100, pet['happiness'] + 5)
    elif action == 'play':
        pet['happiness'] = min(100, pet['happiness'] + 20)
        pet['hunger'] = max(0, pet['hunger'] - 10)
    else:
        return jsonify(ok=False, error='Неизвестное действие'), 404
    return jsonify(ok=True, pet=pet)

@app.get('/api/achievements')
def achievements_get():
    achievements = items()
    return jsonify(ok=True, achievements=achievements, unlocked=sum(a['unlocked'] for a in achievements),
                   total=len(achievements), pet=g.user['pet'], stats=g.user['stats'])

@app.post('/api/settings')
def settings():
    g.user['daily_goal'] = integer(data().get('daily_goal'), 5, 480)
    return jsonify(ok=True)

@app.get('/api/export')
def export():
    response = jsonify(version=1, exported_at=datetime.now(timezone.utc).isoformat(), data=g.user)
    response.headers['Content-Disposition'] = 'attachment; filename=studyflow-progress.json'
    return response

if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG') == '1')
