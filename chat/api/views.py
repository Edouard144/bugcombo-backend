from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache
from chat.models import ChatMessage
from .serializers import ChatMessageSerializer
from duels.models import DuelRoom


class ChatHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, code):
        try:
            room = DuelRoom.objects.get(code=code)
        except DuelRoom.DoesNotExist:
            return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)

        if request.user != room.creator and request.user != room.opponent:
            return Response({'error': 'You are not a player in this room'}, status=status.HTTP_403_FORBIDDEN)

        limit = int(request.query_params.get('limit', 50))
        messages = ChatMessage.objects.filter(room_code=code).select_related('sender').order_by('-created_at')[:limit]

        return Response(ChatMessageSerializer(list(reversed(messages)), many=True).data)


class ChatClearView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, code):
        try:
            room = DuelRoom.objects.get(code=code)
        except DuelRoom.DoesNotExist:
            return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)

        if request.user != room.creator and request.user != room.opponent:
            return Response({'error': 'You are not a player in this room'}, status=status.HTTP_403_FORBIDDEN)

        ChatMessage.objects.filter(room_code=code).delete()
        return Response({'ok': True})
