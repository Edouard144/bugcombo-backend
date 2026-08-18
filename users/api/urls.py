from django.urls import path
from .jwt_views import CustomTokenObtainPairView, CustomTokenRefreshView
from .views import RegisterView, MeView, LeaderboardView, GoogleLoginView, ProfileView, SeasonalLeaderboardView, StatsView, HistoryView, LogoutView, SendFriendRequestView, AcceptFriendRequestView, DeclineFriendRequestView, FriendListView, RemoveFriendView, ActivityFeedView
from .password_reset import PasswordResetRequestView, PasswordResetConfirmView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', MeView.as_view(), name='me'),
    path('stats/', StatsView.as_view(), name='stats'),
    path('history/', HistoryView.as_view(), name='history'),
    path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
    path('leaderboard/seasonal/', SeasonalLeaderboardView.as_view(), name='seasonal_leaderboard'),
    path('google/', GoogleLoginView.as_view(), name='google_login'),
    path('profile/<str:username>/', ProfileView.as_view(), name='profile'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('friends/request/', SendFriendRequestView.as_view(), name='send_friend_request'),
    path('friends/request/<int:request_id>/accept/', AcceptFriendRequestView.as_view(), name='accept_friend_request'),
    path('friends/request/<int:request_id>/decline/', DeclineFriendRequestView.as_view(), name='decline_friend_request'),
    path('friends/', FriendListView.as_view(), name='friend_list'),
    path('friends/<int:user_id>/remove/', RemoveFriendView.as_view(), name='remove_friend'),
    path('activity/', ActivityFeedView.as_view(), name='activity_feed'),
]
