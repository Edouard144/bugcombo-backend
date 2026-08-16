from rest_framework import serializers
from notifications.models import Notification, NotificationPreference

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'type', 'message', 'read', 'created_at']

class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = ['opponent_joined', 'opponent_submitted', 'duel_judged', 'achievement_unlocked', 'email_notifications']
