from django.urls import path
from .views import UserAchievementsView

urlpatterns = [
    path('', UserAchievementsView.as_view(), name='user_achievements'),
]
