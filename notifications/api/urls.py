from django.urls import path
from .views import NotificationListView, MarkNotificationReadView, NotificationPreferenceView

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification-list'),
    path('<int:pk>/read/', MarkNotificationReadView.as_view(), name='notification-read'),
    path('preferences/', NotificationPreferenceView.as_view(), name='notification-preferences'),
]
