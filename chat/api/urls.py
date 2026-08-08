from django.urls import path
from .views import ChatHistoryView, ChatClearView

urlpatterns = [
    path('<str:code>/', ChatHistoryView.as_view(), name='chat_history'),
    path('<str:code>/clear/', ChatClearView.as_view(), name='chat_clear'),
]
