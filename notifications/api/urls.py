from django.urls import path
from .views import NotificationListView, MarkNotificationReadView, MarkAllNotificationsReadView, UnreadNotificationCountView, NotificationPreferenceView

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification-list'),
    path('<int:pk>/read/', MarkNotificationReadView.as_view(), name='notification-read'),
    path('read-all/', MarkAllNotificationsReadView.as_view(), name='notification-read-all'),
    path('unread-count/', UnreadNotificationCountView.as_view(), name='notification-unread-count'),
    path('preferences/', NotificationPreferenceView.as_view(), name='notification-preferences'),
]