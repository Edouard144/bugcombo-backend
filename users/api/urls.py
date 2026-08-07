from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import RegisterView, MeView, LeaderboardView, GoogleLoginView, ProfileView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', MeView.as_view(), name='me'),
    path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
    path('google/', GoogleLoginView.as_view(), name='google_login'),
    path('profile/<str:username>/', ProfileView.as_view(), name='profile'),
]
