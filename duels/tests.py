from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from unittest.mock import patch, MagicMock
import json

User = get_user_model()


class DuelRoomCreationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='creator',
            email='creator@test.com',
            password='testpass123'
        )

    def test_create_duel_returns_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/duels/create/', {
            'language': 'python',
            'difficulty': 'easy'
        })
        self.assertEqual(response.status_code, 201)
        self.assertIn('code', response.data)
        self.assertEqual(len(response.data['code']), 6)

    def test_create_duel_defaults(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/duels/create/', {})
        self.assertEqual(response.status_code, 201)
        self.assertIn('code', response.data)

    def test_create_duel_requires_auth(self):
        response = self.client.post('/api/duels/create/', {})
        self.assertEqual(response.status_code, 401)

    def test_create_duel_sets_creator(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/duels/create/', {})
        self.assertEqual(response.status_code, 201)
        code = response.data['code']
        detail_response = self.client.get(f'/api/duels/{code}/')
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.data['creator']['username'], 'creator')

    def test_create_duel_unique_code(self):
        self.client.force_authenticate(user=self.user)
        response1 = self.client.post('/api/duels/create/', {})
        response2 = self.client.post('/api/duels/create/', {})
        self.assertNotEqual(response1.data['code'], response2.data['code'])


class DuelRoomJoinTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.creator = User.objects.create_user(
            username='creator',
            email='creator@test.com',
            password='testpass123'
        )
        self.opponent = User.objects.create_user(
            username='opponent',
            email='opponent@test.com',
            password='testpass123'
        )

    def test_join_duel(self):
        self.client.force_authenticate(user=self.creator)
        create_response = self.client.post('/api/duels/create/', {})
        code = create_response.data['code']

        self.client.force_authenticate(user=self.opponent)
        response = self.client.post(f'/api/duels/{code}/join/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['ok'])

    def test_join_duel_sets_active_status(self):
        self.client.force_authenticate(user=self.creator)
        create_response = self.client.post('/api/duels/create/', {})
        code = create_response.data['code']

        self.client.force_authenticate(user=self.opponent)
        self.client.post(f'/api/duels/{code}/join/')

        detail_response = self.client.get(f'/api/duels/{code}/')
        self.assertEqual(detail_response.data['status'], 'active')
        self.assertEqual(detail_response.data['opponent']['username'], 'opponent')

    def test_join_own_room_fails(self):
        self.client.force_authenticate(user=self.creator)
        create_response = self.client.post('/api/duels/create/', {})
        code = create_response.data['code']

        response = self.client.post(f'/api/duels/{code}/join/')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)

    def test_join_nonexistent_room(self):
        self.client.force_authenticate(user=self.opponent)
        response = self.client.post('/api/duels/NONEXIST/join/')
        self.assertEqual(response.status_code, 404)

    def test_join_requires_auth(self):
        self.client.force_authenticate(user=self.creator)
        create_response = self.client.post('/api/duels/create/', {})
        code = create_response.data['code']

        self.client.force_authenticate(user=None)
        response = self.client.post(f'/api/duels/{code}/join/')
        self.assertEqual(response.status_code, 401)

    def test_join_already_active_room(self):
        self.client.force_authenticate(user=self.creator)
        create_response = self.client.post('/api/duels/create/', {})
        code = create_response.data['code']

        self.client.force_authenticate(user=self.opponent)
        self.client.post(f'/api/duels/{code}/join/')

        third_user = User.objects.create_user(
            username='third',
            email='third@test.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=third_user)
        response = self.client.post(f'/api/duels/{code}/join/')
        self.assertEqual(response.status_code, 404)


class CodeSubmissionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.creator = User.objects.create_user(
            username='creator',
            email='creator@test.com',
            password='testpass123'
        )
        self.opponent = User.objects.create_user(
            username='opponent',
            email='opponent@test.com',
            password='testpass123'
        )

    def test_submit_code(self):
        self.client.force_authenticate(user=self.creator)
        create_response = self.client.post('/api/duels/create/', {
            'buggy_code': 'print(1/0)'
        })
        code = create_response.data['code']

        self.client.force_authenticate(user=self.opponent)
        self.client.post(f'/api/duels/{code}/join/')

        self.client.force_authenticate(user=self.creator)
        response = self.client.post(f'/api/duels/{code}/submit/', {
            'code': 'try:\n    print(1/0)\nexcept:\n    print("error")'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['ok'])

    def test_submit_twice_fails(self):
        self.client.force_authenticate(user=self.creator)
        create_response = self.client.post('/api/duels/create/', {})
        code = create_response.data['code']

        self.client.force_authenticate(user=self.opponent)
        self.client.post(f'/api/duels/{code}/join/')

        self.client.force_authenticate(user=self.creator)
        self.client.post(f'/api/duels/{code}/submit/', {'code': 'code1'})
        response = self.client.post(f'/api/duels/{code}/submit/', {'code': 'code2'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('already submitted', response.data['error'])

    def test_submit_to_inactive_room(self):
        self.client.force_authenticate(user=self.creator)
        create_response = self.client.post('/api/duels/create/', {})
        code = create_response.data['code']

        response = self.client.post(f'/api/duels/{code}/submit/', {'code': 'some code'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('not active', response.data['error'])

    def test_submit_as_non_player_fails(self):
        self.client.force_authenticate(user=self.creator)
        create_response = self.client.post('/api/duels/create/', {})
        code = create_response.data['code']

        self.client.force_authenticate(user=self.opponent)
        self.client.post(f'/api/duels/{code}/join/')

        outsider = User.objects.create_user(
            username='outsider',
            email='outsider@test.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=outsider)
        response = self.client.post(f'/api/duels/{code}/submit/', {'code': 'hack'})
        self.assertEqual(response.status_code, 403)

    @patch('duels.api.views.judge_submissions')
    def test_full_judging_flow(self, mock_judge):
        mock_judge.return_value = {
            'player1': {
                'correctness': 0.9,
                'cleanliness': 0.8,
                'efficiency': 0.7,
                'security': 0.8,
                'score': 0.8,
                'feedback': 'Good fix'
            },
            'player2': {
                'correctness': 0.8,
                'cleanliness': 0.7,
                'efficiency': 0.6,
                'security': 0.7,
                'score': 0.7,
                'feedback': 'Decent fix'
            },
            'winner': 'player1'
        }

        self.client.force_authenticate(user=self.creator)
        create_response = self.client.post('/api/duels/create/', {
            'language': 'python',
            'difficulty': 'easy',
            'buggy_code': 'print(1/0)'
        })
        code = create_response.data['code']

        self.client.force_authenticate(user=self.opponent)
        self.client.post(f'/api/duels/{code}/join/')

        self.client.force_authenticate(user=self.creator)
        self.client.post(f'/api/duels/{code}/submit/', {
            'code': 'try:\n    print(1/0)\nexcept:\n    print("error")'
        })

        self.client.force_authenticate(user=self.opponent)
        response = self.client.post(f'/api/duels/{code}/submit/', {
            'code': 'print(1/0)'
        })
        if hasattr(response, 'content'):
            print('RESPONSE:', response.status_code, response.content)
        self.assertEqual(response.status_code, 200)

        self.creator.refresh_from_db()
        self.opponent.refresh_from_db()
        self.assertEqual(self.creator.wins, 1)
        self.assertEqual(self.opponent.losses, 1)
        self.assertEqual(self.creator.total_duels, 1)
        self.assertEqual(self.opponent.total_duels, 1)

        detail_response = self.client.get(f'/api/duels/{code}/')
        self.assertEqual(detail_response.data['status'], 'finished')

        submissions_response = self.client.get(f'/api/duels/{code}/submissions/')
        self.assertEqual(len(submissions_response.data), 2)

    @patch('duels.api.views.judge_submissions')
    def test_judging_flow_tie(self, mock_judge):
        mock_judge.return_value = {
            'player1': {
                'correctness': 0.8,
                'cleanliness': 0.8,
                'efficiency': 0.8,
                'security': 0.8,
                'score': 0.8,
                'feedback': 'Good'
            },
            'player2': {
                'correctness': 0.8,
                'cleanliness': 0.8,
                'efficiency': 0.8,
                'security': 0.8,
                'score': 0.8,
                'feedback': 'Good'
            },
            'winner': 'tie'
        }

        self.client.force_authenticate(user=self.creator)
        create_response = self.client.post('/api/duels/create/', {
            'buggy_code': 'x=1'
        })
        code = create_response.data['code']

        self.client.force_authenticate(user=self.opponent)
        self.client.post(f'/api/duels/{code}/join/')

        self.client.force_authenticate(user=self.creator)
        self.client.post(f'/api/duels/{code}/submit/', {'code': 'x = 1'})

        self.client.force_authenticate(user=self.opponent)
        self.client.post(f'/api/duels/{code}/submit/', {'code': 'x=1'})

        self.creator.refresh_from_db()
        self.opponent.refresh_from_db()
        self.assertEqual(self.creator.wins, 0)
        self.assertEqual(self.creator.losses, 0)
        self.assertEqual(self.creator.total_duels, 1)
        self.assertEqual(self.opponent.total_duels, 1)
