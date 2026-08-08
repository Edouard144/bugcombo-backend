import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from duels.models import DuelRoom, Submission


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
        data = json.loads(text_data)
        event_type = data.get('type')

        if event_type == 'room_status':
            room = await self.get_room(self.room_code)
            if room:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {'type': 'room_update', 'status': room['status']}
                )

        elif event_type == 'submitted':
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'player_submitted', 'player': data.get('player', '')}
            )

        elif event_type == 'chat_message':
            message = data.get('message', '').strip()
            if message and len(message) <= 500:
                msg_data = await self.save_chat_message(message)
                if msg_data:
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'chat_broadcast',
                            'message': msg_data['message'],
                            'username': msg_data['username'],
                            'sender_id': msg_data['sender_id'],
                            'created_at': msg_data['created_at'],
                        }
                    )

    async def room_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'room_update',
            'status': event['status']
        }))

    async def player_submitted(self, event):
        await self.send(text_data=json.dumps({
            'type': 'player_submitted',
            'player': event['player']
        }))

    async def duel_judged(self, event):
        await self.send(text_data=json.dumps({
            'type': 'duel_judged'
        }))

    async def chat_broadcast(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'username': event['username'],
            'sender_id': event['sender_id'],
            'created_at': event['created_at'],
        }))

    @database_sync_to_async
    def get_room(self, code):
        try:
            room = DuelRoom.objects.get(code=code)
            return {'status': room.status, 'code': room.code}
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
