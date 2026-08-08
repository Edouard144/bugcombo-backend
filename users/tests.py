from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from unittest.mock import patch
import json

User = get_user_model()


class RegistrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_success(self):
        response = self.client.post('/api/auth/register/', {
            'username': 'newuser',
            'email': 'new@test.com',
            'password': 'newpass123'
        })
        self.assertEqual(response.status_code, 201)
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        self.assertEqual(response.data['user']['email'], 'new@test.com')
        self.assertTrue(User.objects.filter(email='new@test.com').exists())

    def test_register_duplicate_email(self):
        User.objects.create_user(
            username='existing',
            email='existing@test.com',
            password='existingpass123'
        )
        response = self.client.post('/api/auth/register/', {
            'username': 'another',
            'email': 'existing@test.com',
            'password': 'newpass123'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.data)

    def test_register_short_password(self):
        response = self.client.post('/api/auth/register/', {
            'username': 'newuser',
            'email': 'new@test.com',
            'password': 'short'
        })
        self.assertEqual(response.status_code, 400)

    def test_register_missing_fields(self):
        response = self.client.post('/api/auth/register/', {
            'username': 'newuser'
        })
        self.assertEqual(response.status_code, 400)


class LoginTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )

    def test_login_success(self):
        response = self.client.post('/api/auth/login/', {
            'email': 'test@test.com',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_invalid_password(self):
        response = self.client.post('/api/auth/login/', {
            'email': 'test@test.com',
            'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 401)

    def test_login_nonexistent_user(self):
        response = self.client.post('/api/auth/login/', {
            'email': 'nobody@test.com',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 401)

    def test_login_missing_fields(self):
        response = self.client.post('/api/auth/login/', {
            'email': 'test@test.com'
        })
        self.assertEqual(response.status_code, 400)


class MeViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )

    def test_me_authenticated(self):
        refresh_response = self.client.post('/api/auth/login/', {
            'email': 'test@test.com',
            'password': 'testpass123'
        })
        access_token = refresh_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['email'], 'test@test.com')
        self.assertEqual(response.data['username'], 'testuser')

    def test_me_unauthenticated(self):
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, 401)


class LeaderboardTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_leaderboard_returns_top_players(self):
        user1 = User.objects.create_user(username='u1', email='u1@test.com', password='pass1')
        user1.wins = 10
        user1.total_duels = 15
        user1.save()

        user2 = User.objects.create_user(username='u2', email='u2@test.com', password='pass2')
        user2.wins = 5
        user2.total_duels = 10
        user2.save()

        user3 = User.objects.create_user(username='u3', email='u3@test.com', password='pass3')
        user3.wins = 20
        user3.total_duels = 25
        user3.save()

        response = self.client.get('/api/auth/leaderboard/')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        if len(response.data) >= 2:
            self.assertGreaterEqual(response.data[0]['wins'], response.data[1]['wins'])

    def test_leaderboard_empty(self):
        response = self.client.get('/api/auth/leaderboard/')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)

    def test_leaderboard_ordering(self):
        user1 = User.objects.create_user(username='u1', email='u1@test.com', password='pass1')
        user1.wins = 10
        user1.total_duels = 20
        user1.save()

        user2 = User.objects.create_user(username='u2', email='u2@test.com', password='pass2')
        user2.wins = 10
        user2.total_duels = 10
        user2.save()

        response = self.client.get('/api/auth/leaderboard/')
        self.assertEqual(response.status_code, 200)
        if len(response.data) >= 2:
            idx1 = next(i for i, u in enumerate(response.data) if u['username'] == 'u1')
            idx2 = next(i for i, u in enumerate(response.data) if u['username'] == 'u2')
            self.assertLessEqual(idx1, idx2)


class GoogleAuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch('users.api.views.id_token.verify_oauth2_token')
    def test_google_login_new_user(self, mock_verify):
        mock_verify.return_value = {
            'email': 'google@test.com',
            'name': 'Google User',
            'picture': 'https://example.com/pic.jpg'
        }

        response = self.client.post('/api/auth/google/', {
            'token': 'fake_google_token'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('tokens', response.data)
        self.assertTrue(response.data['created'])
        self.assertTrue(User.objects.filter(email='google@test.com').exists())
        self.assertEqual(response.data['user']['email'], 'google@test.com')

    @patch('users.api.views.id_token.verify_oauth2_token')
    def test_google_login_existing_user(self, mock_verify):
        User.objects.create_user(
            username='guser',
            email='existing@test.com',
            password='anypass123'
        )
        mock_verify.return_value = {
            'email': 'existing@test.com',
            'name': 'Existing User',
            'picture': 'https://example.com/pic.jpg'
        }

        response = self.client.post('/api/auth/google/', {
            'token': 'fake_google_token'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('tokens', response.data)
        self.assertFalse(response.data['created'])

    def test_google_login_missing_token(self):
        response = self.client.post('/api/auth/google/', {})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)

    @patch('users.api.views.id_token.verify_oauth2_token')
    def test_google_login_invalid_token(self, mock_verify):
        mock_verify.side_effect = Exception('Invalid token')

        response = self.client.post('/api/auth/google/', {
            'token': 'invalid_token'
        })
        self.assertEqual(response.status_code, 401)
        self.assertIn('error', response.data)
