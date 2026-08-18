from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Replay, ReplayComment

User = get_user_model()

class ReplayCommentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = ReplayComment
        fields = ['id', 'user', 'username', 'text', 'created_at']

class ReplaySerializer(serializers.ModelSerializer):
    comments = ReplayCommentSerializer(many=True, read_only=True)
    creator = serializers.CharField(source='created_by.username', read_only=True)
    room_code = serializers.CharField(source='duel_room.code', read_only=True)

    class Meta:
        model = Replay
        fields = ['id', 'room_code', 'creator', 'events', 'is_public', 'created_at', 'comments']

class ReplayCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Replay
        fields = ['duel_room', 'events', 'is_public']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
