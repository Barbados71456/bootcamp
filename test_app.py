import os
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor

_root = tempfile.TemporaryDirectory()
os.environ['STUDYFLOW_DATA_DIR'] = _root.name
from app import app

class StudyFlowTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def post(self, path, **payload):
        return self.client.post('/api/' + path, json=payload)

    def profile(self):
        return self.client.get('/api/export').json['data']

    def test_all_pages_and_static_assets(self):
        import re
        for page in ('', 'courses', 'kanban', 'timer', 'pet', 'achievements', 'insights'):
            response = self.client.get('/' + page)
            self.assertEqual(response.status_code, 200, page)
            for asset in re.findall(r'(?:src|href)="(/static/[^\"]+)"', response.text):
                with self.client.get(asset) as asset_response:
                    self.assertEqual(asset_response.status_code, 200, asset)

    def test_lesson_idempotency_and_server_duration(self):
        for _ in range(2):
            self.assertEqual(self.post('lesson/complete', course='python-basics', lesson=1, minutes=999).status_code, 200)
        profile = self.profile()
        self.assertEqual(profile['stats']['lessons_done'], 1)
        self.assertEqual(profile['stats']['total_minutes'], 15)
        self.assertEqual(profile['pet']['xp'], 15)
        self.assertEqual(self.post('lesson/complete', course='missing', lesson=1).status_code, 400)

    def test_notes_bookmarks_and_isolation(self):
        self.post('lesson/note', course='html-css', lesson=1, note='<script>alert(1)</script>')
        self.post('lesson/bookmark', course='html-css', lesson=1, bookmark=True)
        self.assertNotIn('<script>alert(1)</script>', self.client.get('/courses').text)
        profile = self.profile()
        self.assertTrue(profile['lessons']['html-css:1']['bookmark'])
        self.assertEqual(app.test_client().get('/api/export').json['data']['lessons'], {})
        # A fresh client with the same signed cookie reads SQLite, without in-memory state.
        other = app.test_client()
        other.set_cookie('session', self.client.get_cookie('session').value)
        self.assertEqual(other.get('/api/export').json['data'], profile)

    def test_task_edit_and_reward_once(self):
        card = self.post('kanban/add', title='Учиться', priority='high', due='2026-11-12').json['card']
        for col in ('done', 'doing', 'done'):
            self.assertEqual(self.post('kanban/move', id=card['id'], to=col).status_code, 200)
        self.assertEqual(self.profile()['pet']['xp'], 12)
        self.post('kanban/edit', id=card['id'], title='Повторить', priority='low', due='')
        self.assertEqual(self.profile()['kanban']['done'][0]['title'], 'Повторить')
        self.post('kanban/delete', id=card['id'])
        self.assertIn('first_task', self.profile()['unlocked'])

    def test_timer_idempotency(self):
        for _ in range(2):
            self.post('timer/finish', id='same-session', minutes=25)
        self.assertEqual(self.profile()['stats']['pomodoros'], 1)
        self.assertEqual(self.profile()['stats']['total_minutes'], 25)

    def test_invalid_inputs_do_not_mutate(self):
        baseline = self.profile()
        for value in (-1, '25', None, True, 121):
            self.assertEqual(self.post('timer/finish', id='test', minutes=value).status_code, 400)
        self.assertEqual(self.post('settings', daily_goal=0).status_code, 400)
        self.assertEqual(self.post('kanban/add', title=4).status_code, 400)
        self.assertEqual(self.post('kanban/add', title='x', column=[]).status_code, 400)
        self.assertEqual(self.post('kanban/add', title='x', due='not-a-date').status_code, 400)
        self.assertEqual(self.client.post('/api/settings', json=[]).status_code, 400)
        self.assertEqual(self.client.post('/api/settings', data='{', content_type='application/json').status_code, 400)
        self.assertEqual(self.profile(), baseline)

    def test_goal_and_pet(self):
        self.assertEqual(self.post('settings', daily_goal=45).status_code, 200)
        self.assertEqual(self.profile()['daily_goal'], 45)
        self.assertEqual(self.post('pet/feed').status_code, 200)
        self.assertEqual(self.post('pet/play').status_code, 200)
        self.post('pet/rename', name='Байт')
        self.assertEqual(self.profile()['pet']['name'], 'Байт')

    def test_concurrent_completions(self):
        self.profile()
        cookie = self.client.get_cookie('session').value
        def complete(_):
            client = app.test_client()
            client.set_cookie('session', cookie)
            return client.post('/api/lesson/complete', json={'course':'git-basics','lesson':1}).status_code
        with ThreadPoolExecutor(max_workers=4) as executor:
            self.assertEqual(list(executor.map(complete, range(4))), [200]*4)
        self.assertEqual(self.profile()['stats']['lessons_done'], 1)

if __name__ == '__main__':
    unittest.main()
