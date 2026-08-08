from django.urls import path
from .views import AuditLogListView, AuditLogDetailView, AuditStatsView

urlpatterns = [
    path('', AuditLogListView.as_view(), name='audit-log-list'),
    path('stats/', AuditStatsView.as_view(), name='audit-log-stats'),
    path('<int:pk>/', AuditLogDetailView.as_view(), name='audit-log-detail'),
]
