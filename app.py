import json
import os
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "studyflow-super-secret-key-change-me")

# ---------- ХРАНИЛИЩЕ (в памяти) ----------
# В реальном проекте замени на БД (SQLite/Postgres).
# Ключ: session_id пользователя
USER_DATA = {}

def get_user():
    """Получить (или создать) данные текущего пользователя."""
    if "uid" not in session:
        session["uid"] = str(uuid.uuid4())
    uid = session["uid"]
    if uid not in USER_DATA:
        USER_DATA[uid] = {
            "pet": {
                "name": "Кодик",
                "level": 1,
                "xp": 0,
                "hunger": 50,
                "happiness": 80,
                "last_fed": datetime.utcnow().isoformat(),
            },
            "kanban": {
                "todo": [],
                "doing": [],
                "done": [],
            },
            "stats": {
                "total_minutes": 0,
                "pomodoros": 0,
                "lessons_done": 0,
            },
        }
    return USER_DATA[uid]

# ---------- КУРСЫ (данные) ----------
COURSES = [
    {
        "id": "vscode-basics",
        "title": "Знакомство с VS Code",
        "icon": "🧩",
        "description": "Установка, интерфейс и первые шаги в Visual Studio Code.",
        "lessons": [
            {"id": 1, "title": "Что такое редактор кода", "minutes": 10,
             "text": "VS Code — бесплатный редактор от Microsoft. Он помогает писать код, подсвечивает ошибки и умеет работать с расширениями."},
            {"id": 2, "title": "Установка VS Code", "minutes": 15,
             "text": "Скачай VS Code с code.visualstudio.com и установи. На Windows запусти установщик, на macOS перетащи в Applications, на Linux используй пакет .deb или .rpm."},
            {"id": 3, "title": "Горячие клавиши", "minutes": 20,
             "text": "Ctrl+P — быстрый переход к файлу. Ctrl+Shift+P — командная палитра. Ctrl+` — терминал. Alt+↑/↓ — переместить строку. Ctrl+/ — закомментировать."},
            {"id": 4, "title": "Полезные расширения", "minutes": 15,
             "text": "Python (Microsoft), Prettier, ESLint, Live Server, GitLens, Russian Language Pack. Установи их через панель Extensions (Ctrl+Shift+X)."},
        ],
    },
    {
        "id": "python-basics",
        "title": "Python: первые шаги",
        "icon": "🐍",
        "description": "Переменные, типы, условия и циклы в Python.",
        "lessons": [
            {"id": 1, "title": "Переменные", "minutes": 15,
             "text": "Переменная — это имя для значения. Пример: x = 5, name = 'Аня'. Python сам определяет тип."},
            {"id": 2, "title": "Типы данных", "minutes": 20,
             "text": "Основные типы: int (числа), float (дроби), str (строки), bool (True/False), list (списки), dict (словари)."},
            {"id": 3, "title": "Условия if/else", "minutes": 20,
             "text": "if x > 0:\n    print('плюс')\nelse:\n    print('минус'). Отступы в Python важны!"},
            {"id": 4, "title": "Циклы", "minutes": 25,
             "text": "for i in range(5): print(i). while x < 10: x += 1. Используй break и continue для управления циклом."},
        ],
    },
    {
        "id": "html-css",
        "title": "HTML и CSS",
        "icon": "🎨",
        "description": "Основа любой веб-страницы — разметка и стили.",
        "lessons": [
            {"id": 1, "title": "Структура HTML", "minutes": 15,
             "text": "<!DOCTYPE html><html><head><title>Заголовок</title></head><body><h1>Привет</h1></body></html>"},
            {"id": 2, "title": "Теги и атрибуты", "minutes": 20,
             "text": "p, a, img, ul/li, div, span. Атрибуты: href, src, class, id, style."},
            {"id": 3, "title": "CSS-селекторы", "minutes": 20,
             "text": "Селектор по тегу: p {}; по классу: .btn {}; по id: #main {}; вложенные: .card p {}."},
            {"id": 4, "title": "Flexbox", "minutes": 25,
             "text": "display: flex; justify-content: center; align-items: center; gap: 10px — выравнивание элементов в ряд или колонку."},
        ],
    },
    {
        "id": "git-basics",
        "title": "Git и GitHub",
        "icon": "🔧",
        "description": "Контроль версий — обязательный навык разработчика.",
        "lessons": [
            {"id": 1, "title": "Что такое Git", "minutes": 10,
             "text": "Git хранит историю изменений файлов. Каждый коммит — это снимок состояния проекта."},
            {"id": 2, "title": "git init и первый коммит", "minutes": 20,
             "text": "git init → git add . → git commit -m 'первый коммит' → git log. Три команды — уже рабочий процесс."},
            {"id": 3, "title": "Ветки", "minutes": 20,
             "text": "git branch feature → git checkout feature → правки → git commit → git merge feature. Ветки позволяют работать над функциями отдельно."},
            {"id": 4, "title": "GitHub и push", "minutes": 15,
             "text": "git remote add origin URL → git push -u origin main. На GitHub можно открыть Pull Request и провести code review."},
        ],
    },
]

# ---------- ДОСТИЖЕНИЯ ----------
ACHIEVEMENTS = [
    {
        "id": "first_lesson",
        "title": "Первый шаг",
        "description": "Заверши свой первый урок",
        "icon": "📖",
        "check": lambda u: u["stats"]["lessons_done"] >= 1,
    },
    {
        "id": "ten_lessons",
        "title": "Ученик",
        "description": "Пройди 10 уроков",
        "icon": "🎓",
        "check": lambda u: u["stats"]["lessons_done"] >= 10,
    },
    {
        "id": "first_pomodoro",
        "title": "Первый помидор",
        "description": "Заверши первую сессию Помодоро",
        "icon": "🍅",
        "check": lambda u: u["stats"]["pomodoros"] >= 1,
    },
    {
        "id": "ten_pomodoros",
        "title": "Продуктивный",
        "description": "Заверши 10 помидоров",
        "icon": "⏱",
        "check": lambda u: u["stats"]["pomodoros"] >= 10,
    },
    {
        "id": "hour_of_study",
        "title": "Час учёбы",
        "description": "Проведи за учёбой 60 минут",
        "icon": "🕐",
        "check": lambda u: u["stats"]["total_minutes"] >= 60,
    },
    {
        "id": "five_hours",
        "title": "Марафонец",
        "description": "Проведи за учёбой 5 часов",
        "icon": "🏃",
        "check": lambda u: u["stats"]["total_minutes"] >= 300,
    },
    {
        "id": "first_task",
        "title": "Организованный",
        "description": "Выполни первую задачу в канбане",
        "icon": "✅",
        "check": lambda u: len(u["kanban"]["done"]) >= 1,
    },
    {
        "id": "five_tasks",
        "title": "Планировщик",
        "description": "Выполни 5 задач в канбане",
        "icon": "📋",
        "check": lambda u: len(u["kanban"]["done"]) >= 5,
    },
    {
        "id": "level_3",
        "title": "Растущий",
        "description": "Достигни 3 уровня питомца",
        "icon": "🌱",
        "check": lambda u: u["pet"]["level"] >= 3,
    },
    {
        "id": "level_5",
        "title": "Опытный",
        "description": "Достигни 5 уровня питомца",
        "icon": "🌟",
        "check": lambda u: u["pet"]["level"] >= 5,
    },
    {
        "id": "level_10",
        "title": "Легенда",
        "description": "Достигни 10 уровня питомца",
        "icon": "👑",
        "check": lambda u: u["pet"]["level"] >= 10,
    },
    {
        "id": "fed_pet",
        "title": "Заботливый",
        "description": "Покорми питомца до 100% сытости",
        "icon": "🍎",
        "check": lambda u: u["pet"]["hunger"] >= 100,
    },
    {
        "id": "happy_pet",
        "title": "Друг",
        "description": "Порадуй питомца до 100% настроения",
        "icon": "😊",
        "check": lambda u: u["pet"]["happiness"] >= 100,
    },
]


def compute_achievements(user):
    """Вернуть список достижений с полем unlocked."""
    result = []
    for a in ACHIEVEMENTS:
        result.append({
            "id": a["id"],
            "title": a["title"],
            "description": a["description"],
            "icon": a["icon"],
            "unlocked": bool(a["check"](user)),
        })
    return result

# ---------- СТРАНИЦЫ ----------

@app.route("/")
def index():
    user = get_user()
    total_lessons = sum(len(c["lessons"]) for c in COURSES)
    return render_template(
        "index.html",
        user=user,
        courses=COURSES,
        total_lessons=total_lessons,
    )

@app.route("/courses")
def courses():
    user = get_user()
    return render_template("courses.html", courses=COURSES, user=user)

@app.route("/kanban")
def kanban():
    user = get_user()
    return render_template("kanban.html", user=user)

@app.route("/timer")
def timer():
    user = get_user()
    return render_template("timer.html", user=user)

@app.route("/pet")
def pet():
    user = get_user()
    return render_template("pet.html", user=user)

@app.route("/achievements")
def achievements():
    user = get_user()
    items = compute_achievements(user)
    unlocked = sum(1 for a in items if a["unlocked"])
    return render_template(
        "achievements.html",
        user=user,
        achievements=items,
        unlocked_count=unlocked,
        total_count=len(items),
    )

# ---------- API: КАНБАН ----------

@app.route("/api/kanban", methods=["GET"])
def api_kanban_get():
    return jsonify(get_user()["kanban"])

@app.route("/api/kanban/add", methods=["POST"])
def api_kanban_add():
    user = get_user()
    data = request.get_json() or {}
    title = (data.get("title") or "").strip()
    column = data.get("column", "todo")
    if not title or column not in ("todo", "doing", "done"):
        return jsonify({"ok": False, "error": "Некорректные данные"}), 400

    card = {"id": str(uuid.uuid4()), "title": title}
    user["kanban"][column].append(card)
    _award_xp(user, 2)
    return jsonify({"ok": True, "card": card, "pet": user["pet"]})

@app.route("/api/kanban/move", methods=["POST"])
def api_kanban_move():
    user = get_user()
    data = request.get_json() or {}
    card_id = data.get("id")
    to_col = data.get("to")
    if to_col not in ("todo", "doing", "done"):
        return jsonify({"ok": False, "error": "Неверная колонка"}), 400

    card = None
    for col in ("todo", "doing", "done"):
        for c in list(user["kanban"][col]):
            if c["id"] == card_id:
                user["kanban"][col].remove(c)
                card = c
                break
        if card:
            break

    if not card:
        return jsonify({"ok": False, "error": "Карточка не найдена"}), 404

    user["kanban"][to_col].append(card)
    if to_col == "done":
        _award_xp(user, 10)
    return jsonify({"ok": True, "pet": user["pet"]})

@app.route("/api/kanban/delete", methods=["POST"])
def api_kanban_delete():
    user = get_user()
    data = request.get_json() or {}
    card_id = data.get("id")
    for col in ("todo", "doing", "done"):
        user["kanban"][col] = [c for c in user["kanban"][col] if c["id"] != card_id]
    return jsonify({"ok": True})

# ---------- API: ТАЙМЕР ----------

@app.route("/api/timer/finish", methods=["POST"])
def api_timer_finish():
    user = get_user()
    data = request.get_json() or {}
    minutes = int(data.get("minutes", 25))
    user["stats"]["total_minutes"] += minutes
    user["stats"]["pomodoros"] += 1
    _award_xp(user, minutes // 5)
    return jsonify({"ok": True, "stats": user["stats"], "pet": user["pet"]})

# ---------- API: ПИТОМЕЦ ----------

@app.route("/api/pet/feed", methods=["POST"])
def api_pet_feed():
    user = get_user()
    p = user["pet"]
    p["hunger"] = min(100, p["hunger"] + 25)
    p["happiness"] = min(100, p["happiness"] + 5)
    _award_xp(user, 3)
    return jsonify({"ok": True, "pet": p})

@app.route("/api/pet/play", methods=["POST"])
def api_pet_play():
    user = get_user()
    p = user["pet"]
    p["happiness"] = min(100, p["happiness"] + 20)
    p["hunger"] = max(0, p["hunger"] - 10)
    return jsonify({"ok": True, "pet": p})

@app.route("/api/pet/rename", methods=["POST"])
def api_pet_rename():
    user = get_user()
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()[:20]
    if name:
        user["pet"]["name"] = name
    return jsonify({"ok": True, "pet": user["pet"]})

# ---------- API: УРОКИ ----------

@app.route("/api/lesson/complete", methods=["POST"])
def api_lesson_complete():
    user = get_user()
    data = request.get_json() or {}
    minutes = int(data.get("minutes", 10))
    user["stats"]["lessons_done"] += 1
    user["stats"]["total_minutes"] += minutes
    _award_xp(user, minutes)
    return jsonify({"ok": True, "pet": user["pet"], "stats": user["stats"]})

# ---------- API: ДОСТИЖЕНИЯ ----------

@app.route("/api/achievements", methods=["GET"])
def api_achievements():
    user = get_user()
    items = compute_achievements(user)
    return jsonify({
        "ok": True,
        "achievements": items,
        "unlocked": sum(1 for a in items if a["unlocked"]),
        "total": len(items),
        "pet": user["pet"],
        "stats": user["stats"],
    })

# ---------- ВСПОМОГАТЕЛЬНОЕ ----------

def _award_xp(user, amount):
    """Начислить XP питомцу и проверить уровень."""
    p = user["pet"]
    p["xp"] += amount
    # 100 XP = 1 уровень
    while p["xp"] >= 100:
        p["xp"] -= 100
        p["level"] += 1
        p["happiness"] = min(100, p["happiness"] + 10)

if __name__ == "__main__":
    app.run(debug=True)