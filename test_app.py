import json
import os
import unittest
import database as db
from app import app

class TestExcuseAI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Temporarily clear cloud connection strings for isolated testing
        cls.orig_db_url = os.environ.pop('DATABASE_URL', None)
        cls.orig_neon_url = os.environ.pop('NEON_DATABASE_URL', None)
        cls.orig_supa_url = os.environ.pop('SUPABASE_URL', None)

        cls.test_db_path = os.path.join(os.path.dirname(__file__), 'test_excuse_ai.db')
        db.DB_PATH = cls.test_db_path
        if os.path.exists(cls.test_db_path):
            os.remove(cls.test_db_path)
        db.init_db()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_db_path):
            os.remove(cls.test_db_path)
        if cls.orig_db_url:
            os.environ['DATABASE_URL'] = cls.orig_db_url
        if cls.orig_neon_url:
            os.environ['NEON_DATABASE_URL'] = cls.orig_neon_url
        if cls.orig_supa_url:
            os.environ['SUPABASE_URL'] = cls.orig_supa_url

    def setUp(self):
        self.app = app
        self.client = self.app.test_client()

    def test_01_registration_validation(self):
        # Missing terms
        res = self.client.post('/api/auth/register', json={
            'name': 'Test User',
            'email': 'testuser@example.com',
            'password': 'password123',
            'confirm_password': 'password123',
            'terms_accepted': False
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn('Terms of Service', res.get_json()['error'])

        # Mismatched password
        res = self.client.post('/api/auth/register', json={
            'name': 'Test User',
            'email': 'testuser@example.com',
            'password': 'password123',
            'confirm_password': 'different_password',
            'terms_accepted': True
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn('match', res.get_json()['error'])

        # Valid registration
        res = self.client.post('/api/auth/register', json={
            'name': 'Jane Doe',
            'email': 'jane.doe@example.com',
            'password': 'securepassword123',
            'confirm_password': 'securepassword123',
            'terms_accepted': True
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertIn('token', data)
        self.assertEqual(data['user']['name'], 'Jane Doe')

        # Duplicate email check
        res_dup = self.client.post('/api/auth/register', json={
            'name': 'Jane Doe',
            'email': 'jane.doe@example.com',
            'password': 'securepassword123',
            'confirm_password': 'securepassword123',
            'terms_accepted': True
        })
        self.assertEqual(res_dup.status_code, 400)
        self.assertIn('already exists', res_dup.get_json()['error'])

    def test_02_login_and_auth(self):
        # Failed login
        res = self.client.post('/api/auth/login', json={
            'email': 'jane.doe@example.com',
            'password': 'wrongpassword'
        })
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.get_json()['error'], 'Incorrect email or password.')

        # Successful login
        res = self.client.post('/api/auth/login', json={
            'email': 'jane.doe@example.com',
            'password': 'securepassword123',
            'remember_me': True
        })
        self.assertEqual(res.status_code, 200)
        token = res.get_json()['token']

        # Get current user /auth/me
        res_me = self.client.get('/api/auth/me', headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(res_me.status_code, 200)
        self.assertEqual(res_me.get_json()['user']['email'], 'jane.doe@example.com')

    def test_03_google_oauth(self):
        res = self.client.post('/api/auth/google', json={
            'name': 'Google Persona',
            'email': 'google.persona@gmail.com',
            'avatar_url': 'https://example.com/avatar.jpg'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('token', data)
        self.assertEqual(data['user']['email'], 'google.persona@gmail.com')

    def test_04_forgot_and_reset_password(self):
        # Forgot password
        res = self.client.post('/api/auth/forgot-password', json={
            'email': 'jane.doe@example.com'
        })
        self.assertEqual(res.status_code, 200)
        token = res.get_json().get('debug_reset_token')
        self.assertIsNotNone(token)

        # Reset password
        res_reset = self.client.post('/api/auth/reset-password', json={
            'token': token,
            'new_password': 'newsecretpassword123',
            'confirm_password': 'newsecretpassword123'
        })
        self.assertEqual(res_reset.status_code, 200)

        # Login with new password
        res_login = self.client.post('/api/auth/login', json={
            'email': 'jane.doe@example.com',
            'password': 'newsecretpassword123'
        })
        self.assertEqual(res_login.status_code, 200)

    def test_05_excuse_generation_and_rewriter(self):
        res_login = self.client.post('/api/auth/login', json={
            'email': 'jane.doe@example.com',
            'password': 'newsecretpassword123'
        })
        token = res_login.get_json()['token']
        headers = {'Authorization': f'Bearer {token}'}

        # Generate excuse
        res_gen = self.client.post('/api/excuses/generate', headers=headers, json={
            'scenario': 'Missed team sprint planning meeting due to sudden flat tire',
            'urgency': 'high',
            'recipient': 'Manager',
            'tone': 'Professional',
            'details': 'Waiting for roadside assistance'
        })
        self.assertEqual(res_gen.status_code, 201)
        excuse = res_gen.get_json()['excuse']
        self.assertIsNotNone(excuse['primary_text'])
        self.assertIn('sprint planning', excuse['primary_text'].lower())
        self.assertGreaterEqual(excuse['believability_score'], 80)
        self.assertGreater(len(excuse['variations']), 0)
        self.assertGreater(len(excuse['tips']), 0)

        # AI Rewrite
        res_rewrite = self.client.post('/api/excuses/rewrite', headers=headers, json={
            'text': excuse['primary_text'],
            'instruction': 'Make it short and direct',
            'tone': 'Short & Direct'
        })
        self.assertEqual(res_rewrite.status_code, 200)
        rewritten = res_rewrite.get_json()['rewritten_text']
        self.assertIsNotNone(rewritten)

        # Favorite
        excuse_id = excuse['id']
        res_fav = self.client.post(f'/api/excuses/{excuse_id}/favorite', headers=headers)
        self.assertEqual(res_fav.status_code, 200)
        self.assertTrue(res_fav.get_json()['is_favorite'])

        # Search excuses
        res_list = self.client.get('/api/excuses?search=sprint', headers=headers)
        self.assertEqual(res_list.status_code, 200)
        self.assertEqual(len(res_list.get_json()['excuses']), 1)

    def test_06_document_generation(self):
        res_login = self.client.post('/api/auth/login', json={
            'email': 'jane.doe@example.com',
            'password': 'newsecretpassword123'
        })
        token = res_login.get_json()['token']
        headers = {'Authorization': f'Bearer {token}'}

        # Formal document generation (Part 3)
        res_doc = self.client.post('/api/documents/generate', headers=headers, json={
            'doc_type': 'Extension Request',
            'title': 'Assignment Extension Request',
            'recipient': 'Professor',
            'issue_date': '26 August 2026',
            'reason': 'Unexpected personal issue',
            'additional_details': 'Need 2 extra days for final project submission'
        })
        self.assertEqual(res_doc.status_code, 201)
        doc = res_doc.get_json()['document']
        self.assertEqual(doc['doc_type'], 'Extension Request')
        self.assertIn('ASSIGNMENT & DEADLINE EXTENSION REQUEST', doc['content']['content_text'])

        # Edit document
        doc_id = doc['id']
        res_edit_doc = self.client.put(f'/api/documents/{doc_id}', headers=headers, json={
            'title': 'Updated Extension Request',
            'content_text': 'Updated document body text.'
        })
        self.assertEqual(res_edit_doc.status_code, 200)
        self.assertEqual(res_edit_doc.get_json()['document']['title'], 'Updated Extension Request')

    def test_07_stats_and_settings(self):
        res_login = self.client.post('/api/auth/login', json={
            'email': 'jane.doe@example.com',
            'password': 'newsecretpassword123'
        })
        token = res_login.get_json()['token']
        headers = {'Authorization': f'Bearer {token}'}

        # Stats
        res_stats = self.client.get('/api/dashboard/stats', headers=headers)
        self.assertEqual(res_stats.status_code, 200)
        stats = res_stats.get_json()['stats']
        self.assertGreaterEqual(stats['total_excuses'], 1)
        self.assertGreaterEqual(stats['total_documents'], 1)

        # Settings
        res_set = self.client.post('/api/user/settings', headers=headers, json={
            'default_tone': 'Formal',
            'default_recipient': 'Professor',
            'theme_preference': 'dark'
        })
        self.assertEqual(res_set.status_code, 200)
        self.assertEqual(res_set.get_json()['settings']['default_tone'], 'Formal')

if __name__ == '__main__':
    unittest.main()
