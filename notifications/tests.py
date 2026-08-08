from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from notifications.models import Notification
from notifications.services import send_notification

User = get_user_model()


class NotificationListTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', email='test@test.com', password='testpass123'
        )
        self.other = User.objects.create_user(
            username='other', email='other@test.com', password='otherpass123'
        )
        self.notification = Notification.objects.create(
            user=self.user, type='opponent_joined', message='Test notification',
        )

    def test_list_notifications(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/notifications/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_list_notifications_requires_auth(self):
        response = self.client.get('/api/notifications/')
        self.assertEqual(response.status_code, 401)

    def test_list_only_own_notifications(self):
        Notification.objects.create(
            user=self.other, type='duel_judged', message='Other notification',
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/notifications/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_list_notifications_ordered_by_newest(self):
        n1 = Notification.objects.create(user=self.user, type='opponent_joined', message='First')
        n2 = Notification.objects.create(user=self.user, type='duel_judged', message='Second')
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/notifications/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['id'], n2.id)
        self.assertEqual(response.data[1]['id'], n1.id)

    def test_list_empty_notifications(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.get('/api/notifications/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])


class MarkNotificationReadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', email='test@test.com', password='testpass123'
        )
        self.other = User.objects.create_user(
            username='other', email='other@test.com', password='otherpass123'
        )
        self.notification = Notification.objects.create(
            user=self.user, type='opponent_joined', message='Test',
        )

    def test_mark_read(self):
        self.assertFalse(self.notification.read)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/notifications/{self.notification.id}/read/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['ok'])
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.read)

    def test_mark_read_nonexistent(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/notifications/9999/read/')
        self.assertEqual(response.status_code, 404)

    def test_mark_read_other_users_notification(self):
        other_notif = Notification.objects.create(
            user=self.other, type='opponent_joined', message='Not yours',
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/notifications/{other_notif.id}/read/')
        self.assertEqual(response.status_code, 404)

    def test_mark_read_requires_auth(self):
        response = self.client.post(f'/api/notifications/{self.notification.id}/read/')
        self.assertEqual(response.status_code, 401)


class NotificationServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', email='test@test.com', password='testpass123'
        )

    def test_send_notification_creates_record(self):
        send_notification(self.user, 'opponent_joined', 'Test message')
        self.assertTrue(
            Notification.objects.filter(user=self.user, type='opponent_joined').exists()
        )
