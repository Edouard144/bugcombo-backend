from django.contrib import admin
from .models import DuelRoom, Submission

@admin.register(DuelRoom)
class DuelRoomAdmin(admin.ModelAdmin):
    list_display = ['code', 'creator', 'opponent', 'status', 'language', 'difficulty', 'created_at']
    list_filter = ['status', 'language', 'difficulty']
    search_fields = ['code', 'creator__email', 'opponent__email']
    readonly_fields = ['id', 'created_at', 'started_at', 'finished_at']

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['room', 'player', 'score', 'is_winner', 'submitted_at']
    list_filter = ['is_winner']
    search_fields = ['player__email', 'room__code']
    readonly_fields = ['id', 'submitted_at']
