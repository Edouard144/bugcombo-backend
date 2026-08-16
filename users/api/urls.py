from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import RegisterView, MeView, LeaderboardView, GoogleLoginView, ProfileView, SeasonalLeaderboardView, StatsView, HistoryView
from .password_reset import PasswordResetRequestView, PasswordResetConfirmView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', MeView.as_view(), name='me'),
    path('stats/', StatsView.as_view(), name='stats'),
    path('history/', HistoryView.as_view(), name='history'),
    path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
    path('leaderboard/seasonal/', SeasonalLeaderboardView.as_view(), name='seasonal_leaderboard'),
    path('google/', GoogleLoginView.as_view(), name='google_login'),
    path('profile/<str:username>/', ProfileView.as_view(), name='profile'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
]
