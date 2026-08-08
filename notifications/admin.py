from django.contrib import admin
from .models import Notification, NotificationPreference

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'type', 'message', 'read', 'created_at']
    list_filter = ['type', 'read', 'created_at']
    search_fields = ['user__username', 'message']

@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'opponent_joined', 'opponent_submitted', 'duel_judged', 'achievement_unlocked', 'email_notifications']
    list_filter = ['opponent_joined', 'opponent_submitted', 'duel_judged', 'achievement_unlocked', 'email_notifications']
    search_fields = ['user__username']
