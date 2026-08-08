from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from chat.models import ChatMessage
from duels.models import DuelRoom

User = get_user_model()


class ChatHistoryTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', email='test@test.com', password='testpass123'
        )
        self.other = User.objects.create_user(
            username='other', email='other@test.com', password='otherpass123'
        )
        self.room = DuelRoom.objects.create(
            creator=self.user, opponent=self.other,
            code='ROOM01', language='python', difficulty='easy', status='active',
        )
        self.message = ChatMessage.objects.create(
            room_code=self.room.code, sender=self.user, message='Hello!',
        )

    def test_get_chat_history(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/chat/{self.room.code}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['message'], 'Hello!')

    def test_chat_history_requires_auth(self):
        response = self.client.get(f'/api/chat/{self.room.code}/')
        self.assertEqual(response.status_code, 401)

    def test_chat_history_room_not_found(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/chat/INVALID/')
        self.assertEqual(response.status_code, 404)

    def test_chat_history_not_participant(self):
        outsider = User.objects.create_user(
            username='outsider', email='outsider@test.com', password='pass123'
        )
        self.client.force_authenticate(user=outsider)
        response = self.client.get(f'/api/chat/{self.room.code}/')
        self.assertEqual(response.status_code, 403)

    def test_chat_history_empty(self):
        self.client.force_authenticate(user=self.user)
        ChatMessage.objects.all().delete()
        response = self.client.get(f'/api/chat/{self.room.code}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_chat_history_ordered_by_time(self):
        m1 = ChatMessage.objects.create(room_code=self.room.code, sender=self.user, message='First')
        m2 = ChatMessage.objects.create(room_code=self.room.code, sender=self.user, message='Second')
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/chat/{self.room.code}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['message'], 'First')
        self.assertEqual(response.data[1]['message'], 'Second')

    def test_chat_history_with_limit(self):
        for i in range(10):
            ChatMessage.objects.create(room_code=self.room.code, sender=self.user, message=f'Msg {i}')
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/chat/{self.room.code}/?limit=3')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)


class ChatClearTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', email='test@test.com', password='testpass123'
        )
        self.other = User.objects.create_user(
            username='other', email='other@test.com', password='otherpass123'
        )
        self.room = DuelRoom.objects.create(
            creator=self.user, opponent=self.other,
            code='ROOM01', language='python', difficulty='easy', status='active',
        )
        self.message = ChatMessage.objects.create(
            room_code=self.room.code, sender=self.user, message='Hello!',
        )

    def test_clear_chat(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f'/api/chat/{self.room.code}/clear/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['ok'])
        self.assertEqual(ChatMessage.objects.filter(room_code=self.room.code).count(), 0)

    def test_clear_chat_requires_auth(self):
        response = self.client.delete(f'/api/chat/{self.room.code}/clear/')
        self.assertEqual(response.status_code, 401)

    def test_clear_chat_room_not_found(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete('/api/chat/INVALID/clear/')
        self.assertEqual(response.status_code, 404)

    def test_clear_chat_not_participant(self):
        outsider = User.objects.create_user(
            username='outsider', email='outsider@test.com', password='pass123'
        )
        self.client.force_authenticate(user=outsider)
        response = self.client.delete(f'/api/chat/{self.room.code}/clear/')
        self.assertEqual(response.status_code, 403)

    def test_clear_only_room_messages(self):
        ChatMessage.objects.create(room_code='OTHER01', sender=self.user, message='Other msg')
        self.client.force_authenticate(user=self.user)
        self.client.delete(f'/api/chat/{self.room.code}/clear/')
        self.assertEqual(ChatMessage.objects.filter(room_code=self.room.code).count(), 0)
        self.assertEqual(ChatMessage.objects.filter(room_code='OTHER01').count(), 1)
