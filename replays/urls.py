from django.urls import path
from .views import ReplayListView, ReplayDetailView, ReplayCommentView, MyReplaysView

urlpatterns = [
    path('', ReplayListView.as_view(), name='replay_list'),
    path('<int:replay_id>/', ReplayDetailView.as_view(), name='replay_detail'),
    path('<int:replay_id>/comments/', ReplayCommentView.as_view(), name='replay_comment'),
    path('my/', MyReplaysView.as_view(), name='my_replays'),
]
