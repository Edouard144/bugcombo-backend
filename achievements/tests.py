from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from achievements.models import Achievement

User = get_user_model()


class UserAchievementsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', email='test@test.com', password='testpass123'
        )
        self.other = User.objects.create_user(
            username='other', email='other@test.com', password='otherpass123'
        )
        self.achievement = Achievement.objects.create(
            name='First Win', description='Win your first duel',
            icon='trophy', condition='first_win',
        )
        self.ten_win = Achievement.objects.create(
            name='Ten Wins', description='Win 10 duels',
            icon='star', condition='ten_wins',
        )

    def test_list_achievements(self):
        self.user.achievements.add(self.achievement)
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/achievements/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'First Win')

    def test_list_achievements_requires_auth(self):
        response = self.client.get('/api/achievements/')
        self.assertEqual(response.status_code, 401)

    def test_list_empty_achievements(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/achievements/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_only_own_achievements(self):
        self.user.achievements.add(self.achievement)
        self.other.achievements.add(self.ten_win)
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/achievements/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_multiple_achievements(self):
        self.user.achievements.add(self.achievement, self.ten_win)
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/achievements/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)


class AchievementModelTests(TestCase):
    def test_achievement_str(self):
        a = Achievement.objects.create(
            name='First Win', description='Desc', icon='trophy', condition='first_win',
        )
        self.assertEqual(str(a), 'First Win')

    def test_achievement_fields(self):
        a = Achievement.objects.create(
            name='First Win', description='Win your first duel',
            icon='trophy', condition='first_win',
        )
        self.assertEqual(a.name, 'First Win')
        self.assertEqual(a.description, 'Win your first duel')
        self.assertEqual(a.icon, 'trophy')
        self.assertEqual(a.condition, 'first_win')
