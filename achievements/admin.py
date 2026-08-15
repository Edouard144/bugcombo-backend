from django.contrib import admin
from .models import Achievement

@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['name', 'condition_type', 'condition_value', 'icon']
    search_fields = ['name', 'description']
