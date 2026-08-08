from django.urls import path
from .views import BugListCreateView, BugDetailView, FeaturedBugsView, RandomBugView

urlpatterns = [
    path('', BugListCreateView.as_view(), name='bug-list'),
    path('featured/', FeaturedBugsView.as_view(), name='bug-featured'),
    path('random/', RandomBugView.as_view(), name='bug-random'),
    path('<uuid:pk>/', BugDetailView.as_view(), name='bug-detail'),
]
