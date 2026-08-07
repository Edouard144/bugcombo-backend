from django.urls import path
from .views import CreateDuelView, JoinDuelView, DuelDetailView, SubmitCodeView, RoomSubmissionsView, RematchView

urlpatterns = [
    path('create/', CreateDuelView.as_view(), name='create_duel'),
    path('<str:code>/join/', JoinDuelView.as_view(), name='join_duel'),
    path('<str:code>/submit/', SubmitCodeView.as_view(), name='submit_code'),
    path('<str:code>/submissions/', RoomSubmissionsView.as_view(), name='room_submissions'),
    path('<str:code>/rematch/', RematchView.as_view(), name='rematch'),
    path('<str:code>/', DuelDetailView.as_view(), name='duel_detail'),
]