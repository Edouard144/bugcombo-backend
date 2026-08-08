from rest_framework import serializers
from notifications.models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'type', 'message', 'read', 'created_at']

class NotificationPreferenceSerializer(serializers.Serializer):
    email_opponent_joined = serializers.BooleanField(default=True)
    email_duel_judged = serializers.BooleanField(default=True)
    email_achievement_unlocked = serializers.BooleanField(default=True)
    push_notifications = serializers.BooleanField(default=True)
