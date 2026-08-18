from django.urls import path
from .views import SnippetListView, SnippetDetailView, LikeSnippetView, UnlikeSnippetView, MySnippetsView

urlpatterns = [
    path('', SnippetListView.as_view(), name='snippet_list'),
    path('<int:snippet_id>/', SnippetDetailView.as_view(), name='snippet_detail'),
    path('<int:snippet_id>/like/', LikeSnippetView.as_view(), name='like_snippet'),
    path('<int:snippet_id>/unlike/', UnlikeSnippetView.as_view(), name='unlike_snippet'),
    path('my/', MySnippetsView.as_view(), name='my_snippets'),
]
