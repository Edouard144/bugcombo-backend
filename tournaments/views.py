from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Tournament, TournamentParticipant, TournamentMatch
from .serializers import TournamentSerializer, TournamentCreateSerializer, TournamentParticipantSerializer, BracketMatchSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, OpenApiResponse
import random

class TournamentListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Tournaments'],
        summary='List tournaments',
        description='List all tournaments with optional filtering by status.',
        parameters=[
            OpenApiParameter(name='status', description='Filter by status', required=False, type=str, enum=['upcoming', 'ongoing', 'completed', 'cancelled']),
            OpenApiParameter(name='page', description='Page number', required=False, type=int),
            OpenApiParameter(name='limit', description='Items per page', required=False, type=int),
        ],
        responses={200: OpenApiResponse(response=TournamentSerializer(many=True))}
    )
    def get(self, request):
        tournaments = Tournament.objects.all()
        status_filter = request.query_params.get('status')
        if status_filter:
            tournaments = tournaments.filter(status=status_filter)
        
        page = int(request.query_params.get('page', 1))
        limit = int(request.query_params.get('limit', 20))
        start = (page - 1) * limit
        end = start + limit
        total = tournaments.count()
        page_tournaments = tournaments[start:end]
        serializer = TournamentSerializer(page_tournaments, many=True)
        return Response({
            'count': total,
            'page': page,
            'limit': limit,
            'results': serializer.data
        })

class CreateTournamentView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Tournaments'],
        summary='Create tournament',
        description='Create a new tournament. Creator becomes first participant.',
        request=TournamentCreateSerializer,
        responses={
            201: OpenApiResponse(response=TournamentSerializer),
            400: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Validation error'),
        }
    )
    def post(self, request):
        serializer = TournamentCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            tournament = serializer.save()
            TournamentParticipant.objects.create(
                tournament=tournament,
                user=request.user,
                status='registered',
                seed=1
            )
            return Response(TournamentSerializer(tournament).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TournamentDetailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Tournaments'],
        summary='Tournament detail',
        description='Get tournament details including participants and matches.',
        parameters=[
            OpenApiParameter(name='tournament_id', description='Tournament ID', required=True, type=int, location=OpenApiParameter.PATH)
        ],
        responses={
            200: OpenApiResponse(response=TournamentSerializer),
            404: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Tournament not found'),
        }
    )
    def get(self, request, tournament_id):
        tournament = get_object_or_404(Tournament, id=tournament_id)
        serializer = TournamentSerializer(tournament)
        return Response(serializer.data)

class RegisterForTournamentView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Tournaments'],
        summary='Register for tournament',
        description='Register the authenticated user for a tournament.',
        parameters=[
            OpenApiParameter(name='tournament_id', description='Tournament ID', required=True, type=int, location=OpenApiParameter.PATH)
        ],
        responses={
            201: OpenApiResponse(response=TournamentParticipantSerializer),
            400: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Registration closed or already registered'),
            404: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Tournament not found'),
        }
    )
    def post(self, request, tournament_id):
        tournament = get_object_or_404(Tournament, id=tournament_id)
        
        if tournament.status != 'upcoming':
            return Response({'error': 'Registration is closed'}, status=status.HTTP_400_BAD_REQUEST)
        
        if timezone.now() > tournament.registration_end:
            return Response({'error': 'Registration period has ended'}, status=status.HTTP_400_BAD_REQUEST)
        
        existing = TournamentParticipant.objects.filter(tournament=tournament, user=request.user).first()
        if existing:
            return Response({'error': 'Already registered'}, status=status.HTTP_400_BAD_REQUEST)
        
        current_count = tournament.participants.count()
        if current_count >= tournament.max_participants:
            return Response({'error': 'Tournament is full'}, status=status.HTTP_400_BAD_REQUEST)
        
        seed = current_count + 1
        participant = TournamentParticipant.objects.create(
            tournament=tournament,
            user=request.user,
            status='registered',
            seed=seed
        )
        return Response(TournamentParticipantSerializer(participant).data, status=status.HTTP_201_CREATED)

class StartTournamentView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Tournaments'],
        summary='Start tournament',
        description='Start a tournament and generate bracket matches. Only creator can start.',
        parameters=[
            OpenApiParameter(name='tournament_id', description='Tournament ID', required=True, type=int, location=OpenApiParameter.PATH)
        ],
        responses={
            200: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Tournament started'),
            400: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Cannot start tournament'),
            403: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Only creator can start'),
            404: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Tournament not found'),
        }
    )
    def post(self, request, tournament_id):
        tournament = get_object_or_404(Tournament, id=tournament_id)
        
        if tournament.creator != request.user:
            return Response({'error': 'Only the creator can start the tournament'}, status=status.HTTP_403_FORBIDDEN)
        
        if tournament.status != 'upcoming':
            return Response({'error': 'Tournament has already started or finished'}, status=status.HTTP_400_BAD_REQUEST)
        
        participants = list(TournamentParticipant.objects.filter(tournament=tournament, status='registered'))
        if len(participants) < tournament.min_participants:
            return Response({'error': f'Minimum {tournament.min_participants} participants required'}, status=status.HTTP_400_BAD_REQUEST)
        
        tournament.status = 'ongoing'
        tournament.save()
        
        self._generate_bracket(tournament, participants)
        
        return Response({'message': 'Tournament started', 'tournament': TournamentSerializer(tournament).data})

    def _generate_bracket(self, tournament, participants):
        random.shuffle(participants)
        num_participants = len(participants)
        next_power_of_2 = 1
        while next_power_of_2 < num_participants:
            next_power_of_2 *= 2
        
        bracket_size = next_power_of_2
        matches_in_round = bracket_size // 2
        
        for match_num in range(1, matches_in_round + 1):
            p1_index = (match_num - 1) * 2
            p2_index = (match_num - 1) * 2 + 1
            
            participant1 = participants[p1_index] if p1_index < num_participants else None
            participant2 = participants[p2_index] if p2_index < num_participants else None
            
            TournamentMatch.objects.create(
                tournament=tournament,
                round=1,
                match_number=match_num,
                participant1=participant1.user if participant1 else None,
                participant2=participant2.user if participant2 else None,
            )

class TournamentBracketView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Tournaments'],
        summary='Tournament bracket',
        description='Get the full bracket for a tournament with all matches.',
        parameters=[
            OpenApiParameter(name='tournament_id', description='Tournament ID', required=True, type=int, location=OpenApiParameter.PATH)
        ],
        responses={
            200: OpenApiResponse(response=BracketMatchSerializer(many=True)),
            404: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Tournament not found'),
        }
    )
    def get(self, request, tournament_id):
        tournament = get_object_or_404(Tournament, id=tournament_id)
        matches = tournament.matches.select_related('participant1', 'participant2', 'winner', 'loser', 'duel_room').order_by('round', 'match_number')
        serializer = BracketMatchSerializer(matches, many=True)
        return Response(serializer.data)

class MyTournamentsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Tournaments'],
        summary='My tournaments',
        description='Get tournaments the authenticated user is participating in.',
        responses={200: OpenApiResponse(response=TournamentSerializer(many=True))}
    )
    def get(self, request):
        participants = TournamentParticipant.objects.filter(user=request.user).select_related('tournament')
        tournaments = [p.tournament for p in participants]
        serializer = TournamentSerializer(tournaments, many=True)
        return Response(serializer.data)
