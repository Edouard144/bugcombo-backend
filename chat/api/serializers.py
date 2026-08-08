from rest_framework import serializers
from chat.models import ChatMessage
from users.api.serializers import UserSerializer


class ChatMessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    username = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = ['id', 'room_code', 'sender', 'username', 'message', 'created_at']

    def get_username(self, obj):
        if obj.sender:
            return obj.sender.username
        return ''


class ChatMessageCreateSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=500)
