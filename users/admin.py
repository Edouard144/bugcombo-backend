from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.urls import path
from django.shortcuts import render
from .models import User
from duels.models import DuelRoom, Submission

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'total_duels', 'wins', 'losses', 'is_staff', 'is_active']
    list_filter = ['is_staff', 'is_superuser', 'is_active']
    search_fields = ['email', 'username']
    ordering = ['-wins', '-total_duels']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Stats', {'fields': ('bio', 'total_duels', 'wins', 'losses')}),
    )
    actions = ['ban_users', 'unban_users']

    @admin.action(description='Ban selected users')
    def ban_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} users banned successfully.')

    @admin.action(description='Unban selected users')
    def unban_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} users unbanned successfully.')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_site.admin_view(self.dashboard_view), name='users_dashboard'),
        ]
        return custom_urls + urls

    def dashboard_view(self, request):
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        total_duels = DuelRoom.objects.count()
        total_submissions = Submission.objects.count()
        top_players = User.objects.order_by('-wins', '-total_duels')[:10]

        context = {
            'total_users': total_users,
            'active_users': active_users,
            'total_duels': total_duels,
            'total_submissions': total_submissions,
            'top_players': top_players,
            'title': 'User Dashboard',
        }
        return render(request, 'admin/user_dashboard.html', context)
