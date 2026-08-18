from django.urls import path
from .views import PracticeRoomListView, PracticeRoomDetailView, PracticeSubmitView

urlpatterns = [
    path('', PracticeRoomListView.as_view(), name='practice_list'),
    path('<int:room_id>/', PracticeRoomDetailView.as_view(), name='practice_detail'),
    path('<int:room_id>/submit/', PracticeSubmitView.as_view(), name='practice_submit'),
]
