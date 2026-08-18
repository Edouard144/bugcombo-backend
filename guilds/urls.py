from django.urls import path
from .views import GuildListView, CreateGuildView, GuildDetailView, JoinGuildView, LeaveGuildView, MyGuildView, GuildEventListView, CreateGuildEventView, GuildWarListView

urlpatterns = [
    path('', GuildListView.as_view(), name='guild_list'),
    path('create/', CreateGuildView.as_view(), name='create_guild'),
    path('<int:guild_id>/', GuildDetailView.as_view(), name='guild_detail'),
    path('<int:guild_id>/join/', JoinGuildView.as_view(), name='join_guild'),
    path('<int:guild_id>/leave/', LeaveGuildView.as_view(), name='leave_guild'),
    path('my/', MyGuildView.as_view(), name='my_guild'),
    path('<int:guild_id>/events/', GuildEventListView.as_view(), name='guild_events'),
    path('<int:guild_id>/events/create/', CreateGuildEventView.as_view(), name='create_guild_event'),
    path('<int:guild_id>/wars/', GuildWarListView.as_view(), name='guild_wars'),
]
