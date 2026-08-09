from django.contrib import admin
from .models import DuelRoom, Submission

@admin.register(DuelRoom)
class DuelRoomAdmin(admin.ModelAdmin):
    list_display = ['code', 'creator', 'opponent', 'status', 'language', 'difficulty', 'archived', 'created_at']
    list_filter = ['status', 'language', 'difficulty', 'archived']
    search_fields = ['code', 'creator__email', 'opponent__email']
    readonly_fields = ['id', 'created_at', 'started_at', 'finished_at']
    actions = ['archive_duels', 'unarchive_duels']

    @admin.action(description='Archive selected duels')
    def archive_duels(self, request, queryset):
        updated = queryset.update(archived=True)
        self.message_user(request, f'{updated} duels archived successfully.')

    @admin.action(description='Unarchive selected duels')
    def unarchive_duels(self, request, queryset):
        updated = queryset.update(archived=False)
        self.message_user(request, f'{updated} duels unarchived successfully.')

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['room', 'player', 'score', 'is_winner', 'submitted_at']
    list_filter = ['is_winner']
    search_fields = ['player__email', 'room__code']
    readonly_fields = ['id', 'submitted_at']
