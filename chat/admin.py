from django.contrib import admin
from chat.models import ChatMessage


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'room_code', 'message', 'created_at']
    list_filter = ['created_at']
    search_fields = ['sender__email', 'room_code', 'message']
    readonly_fields = ['id', 'created_at']
