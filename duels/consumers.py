import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from duels.models import DuelRoom, Submission
from notifications.services import send_notification

logger = logging.getLogger('duels.websocket')


class DuelConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_code = self.scope['url_route']['kwargs']['room_code']
        self.room_group_name = f'duel_{self.room_code}'

        user = self.scope.get('user')
        if not user or user.is_anonymous:
            await self.close(code=4001)
            return

        self.user = user
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        await self.send(text_data=json.dumps({
            'type': 'connected',
            'message': f'Connected to duel room {self.room_code}'
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        event_type = data.get('type')

        if event_type == 'room_status':
            room = await self.get_room(self.room_code)
            if room:
                await self.send(text_data=json.dumps({
                    'type': 'room_status',
                    'status': room['status'],
                    'code': room['code'],
                    'language': room['language'],
                    'difficulty': room['difficulty'],
                    'duration': room['duration'],
                    'started_at': room['started_at'],
                    'finished_at': room['finished_at'],
                }))

        elif event_type == 'submitted':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'submitted',
                    'player': data.get('player', ''),
                    'timestamp': data.get('timestamp')
                }
            )

    async def room_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'room_update',
            'status': event['status'],
            'code': event.get('code', self.room_code)
        }))

    async def submitted(self, event):
        await self.send(text_data=json.dumps({
            'type': 'submitted',
            'player': event['player'],
            'timestamp': event.get('timestamp')
        }))

    async def opponent_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'opponent_update',
            'action': event['action'],
            'username': event['username']
        }))

    async def opponent_submitted(self, event):
        await self.send(text_data=json.dumps({
            'type': 'opponent_submitted',
            'username': event['username']
        }))

    async def duel_judged(self, event):
        await self.send(text_data=json.dumps({
            'type': 'duel_judged',
            'winner': event.get('winner'),
            'score': event.get('score'),
            'submissions': event.get('submissions', [])
        }))

    @database_sync_to_async
    def get_room(self, code):
        try:
            room = DuelRoom.objects.select_related('creator', 'opponent').get(code=code)
            return {
                'code': room.code,
                'status': room.status,
                'language': room.language,
                'difficulty': room.difficulty,
                'duration': room.duration,
                'started_at': room.started_at.isoformat() if room.started_at else None,
                'finished_at': room.finished_at.isoformat() if room.finished_at else None,
            }
        except DuelRoom.DoesNotExist:
            return None

    @database_sync_to_async
    def save_chat_message(self, message):
        from chat.models import ChatMessage
        msg = ChatMessage.objects.create(
            room_code=self.room_code,
            sender=self.user,
            message=message,
        )
        return {
            'message': msg.message,
            'username': self.user.username,
            'sender_id': str(self.user.id),
            'created_at': msg.created_at.isoformat(),
        }
