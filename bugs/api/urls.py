from django.urls import path
from .views import BugListCreateView, BugDetailView

urlpatterns = [
    path('', BugListCreateView.as_view(), name='bug-list'),
    path('<uuid:pk>/', BugDetailView.as_view(), name='bug-detail'),
]
