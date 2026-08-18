from django.urls import path
from .views import BadgeListView, UserBadgesView, DailyRewardsView, UserStreakView

urlpatterns = [
    path('badges/', BadgeListView.as_view(), name='badge_list'),
    path('my/badges/', UserBadgesView.as_view(), name='user_badges'),
    path('daily-rewards/', DailyRewardsView.as_view(), name='daily_rewards'),
    path('streak/', UserStreakView.as_view(), name='user_streak'),
]
