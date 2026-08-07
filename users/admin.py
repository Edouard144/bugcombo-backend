from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'total_duels', 'wins', 'losses', 'is_staff']
    list_filter = ['is_staff', 'is_superuser', 'is_active']
    search_fields = ['email', 'username']
    ordering = ['-wins', '-total_duels']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Stats', {'fields': ('bio', 'total_duels', 'wins', 'losses')}),
    )
