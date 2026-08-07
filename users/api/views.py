from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.cache import cache
from django.db.models import Q
from google.oauth2 import id_token
from google.auth.transport import requests
from duels.models import DuelRoom, Submission
from .serializers import RegisterSerializer, UserSerializer, MatchHistorySerializer, ProfileStatsSerializer

User = get_user_model()

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

class LeaderboardView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        cache_key = 'leaderboard_top10'
        data = cache.get(cache_key)
        if data is None:
            players = User.objects.order_by('-wins', '-total_duels')[:10]
            data = UserSerializer(players, many=True).data
            cache.set(cache_key, data, 30)
        return Response(data)

class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response({'error': 'Token is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            idinfo = id_token.verify_oauth2_token(token, requests.Request(), settings.GOOGLE_CLIENT_ID)
            email = idinfo['email']
            name = idinfo.get('name', '')
            picture = idinfo.get('picture', '')
        except Exception:
            return Response({'error': 'Invalid Google token'}, status=status.HTTP_401_UNAUTHORIZED)

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': name.replace(' ', '_').lower() + str(hash(email) % 10000),
                'bio': f'Google user: {name}',
            }
        )

        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'created': created,
        })

class ProfileView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        total = user.total_duels
        wins = user.wins
        losses = user.losses
        win_rate = (wins / total * 100) if total > 0 else 0.0

        rooms = DuelRoom.objects.select_related('creator', 'opponent').filter(
            Q(creator=user) | Q(opponent=user),
            status='finished'
        ).order_by('-finished_at')[:10]

        matches = []
        for room in rooms:
            opponent = room.opponent if room.creator == user else room.creator
            submission = Submission.objects.filter(room=room, player=user).first()
            result = 'win' if submission and submission.is_winner else 'loss'
            score = submission.score if submission else 0.0

            matches.append({
                'opponent': opponent.username if opponent else 'Unknown',
                'result': result,
                'score': score,
                'date': room.finished_at
            })

        return Response({
            'stats': ProfileStatsSerializer({
                'wins': wins,
                'losses': losses,
                'total_duels': total,
                'win_rate': round(win_rate, 2)
            }).data,
            'matches': MatchHistorySerializer(matches, many=True).data
        })
