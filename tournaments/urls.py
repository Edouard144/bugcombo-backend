from django.urls import path
from .views import TournamentListView, CreateTournamentView, TournamentDetailView, RegisterForTournamentView, StartTournamentView, TournamentBracketView, MyTournamentsView

urlpatterns = [
    path('', TournamentListView.as_view(), name='tournament_list'),
    path('create/', CreateTournamentView.as_view(), name='create_tournament'),
    path('<int:tournament_id>/', TournamentDetailView.as_view(), name='tournament_detail'),
    path('<int:tournament_id>/register/', RegisterForTournamentView.as_view(), name='register_tournament'),
    path('<int:tournament_id>/start/', StartTournamentView.as_view(), name='start_tournament'),
    path('<int:tournament_id>/bracket/', TournamentBracketView.as_view(), name='tournament_bracket'),
    path('my/', MyTournamentsView.as_view(), name='my_tournaments'),
]
