from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken, OutstandingToken, BlacklistedToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.cache import cache
from django.db.models import Prefetch, Q, Count
from django.utils import timezone
from google.oauth2 import id_token
from google.auth.transport import requests
from duels.models import DuelRoom, Submission
from users.models import FriendRequest, Activity
from .serializers import RegisterSerializer, UserSerializer, UserUpdateSerializer, AuthResponseSerializer, ProfileStatsSerializer, ProfileResponseSerializer, UserStatsSerializer, MatchHistorySerializer, SeasonalLeaderboardEntrySerializer, FriendRequestSerializer, ActivitySerializer, FriendSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, OpenApiResponse
import hashlib

User = get_user_model()

class RegisterThrottle(AnonRateThrottle):
    rate = '5/hour'

    def allow_request(self, request, view):
        if getattr(settings, 'TESTING', False):
            return True
        return super().allow_request(request, view)

class GoogleLoginThrottle(AnonRateThrottle):
    rate = '10/hour'

    def allow_request(self, request, view):
        if getattr(settings, 'TESTING', False):
            return True
        return super().allow_request(request, view)

class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [RegisterThrottle]

    @extend_schema(
        tags=['Auth'],
        summary='Register a new user',
        description='Create a new user account with email, username, and password. Returns JWT access and refresh tokens on successful registration.',
        request=RegisterSerializer,
        responses={
            201: OpenApiResponse(response=AuthResponseSerializer, description='User created successfully'),
            400: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Validation error'),
        }
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LeaderboardView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Users'],
        summary='Top 10 leaderboard',
        description='Get the top 10 players ranked by wins and total duels. Results are cached for 60 seconds.',
        responses={200: OpenApiResponse(response=UserSerializer(many=True))}
    )
    def get(self, request):
        cache_key = 'leaderboard_top10'
        data = cache.get(cache_key)
        if data is None:
            players = User.objects.order_by('-wins', '-total_duels')[:10]
            data = UserSerializer(players, many=True).data
            cache.set(cache_key, data, 60)
        return Response(data)

def invalidate_leaderboard_cache():
    cache.delete('leaderboard_top10')

class SeasonalLeaderboardView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Users'],
        summary='Seasonal leaderboard',
        description='Get the top 10 players for the current month ranked by wins. Results are cached for 60 seconds.',
        responses={200: OpenApiResponse(response=SeasonalLeaderboardEntrySerializer(many=True))}
    )
    def get(self, request):
        cache_key = 'leaderboard_seasonal'
        data = cache.get(cache_key)
        if data is None:
            now = timezone.now()
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            seasonal_winners = Submission.objects.filter(
                room__finished_at__gte=month_start,
                is_winner=True
            ).values('player').annotate(
                seasonal_wins=Count('id')
            ).order_by('-seasonal_wins')[:10]

            user_ids = [entry['player'] for entry in seasonal_winners]
            users = User.objects.in_bulk(user_ids)

            leaderboard = []
            for entry in seasonal_winners:
                user = users[entry['player']]
                leaderboard.append({
                    'id': user.id,
                    'username': user.username,
                    'seasonal_wins': entry['seasonal_wins'],
                    'total_duels': user.total_duels,
                    'current_streak': user.current_streak,
                    'best_streak': user.best_streak,
                })
            data = leaderboard
            cache.set(cache_key, data, 60)
        return Response(data)

def invalidate_seasonal_leaderboard_cache():
    cache.delete('leaderboard_seasonal')

class GoogleLoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [GoogleLoginThrottle]

    @extend_schema(
        tags=['Auth'],
        summary='Login with Google',
        description='Authenticate using a Google OAuth2 ID token. Creates a new user account if one does not already exist with the provided email.',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'token': {'type': 'string', 'description': 'Google OAuth2 ID token'}
                },
                'required': ['token']
            }
        },
        responses={
            200: OpenApiResponse(response=AuthResponseSerializer, description='Login successful'),
            401: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Invalid Google token'),
        }
    )
    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response({'error': 'Token is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            idinfo = id_token.verify_oauth2_token(token, requests.Request(), settings.GOOGLE_CLIENT_ID)
            email = idinfo['email']
            name = idinfo.get('name', '')
        except Exception:
            return Response({'error': 'Invalid Google token'}, status=status.HTTP_401_UNAUTHORIZED)

        suffix = hashlib.md5(email.encode()).hexdigest()[:6]
        base_username = name.replace(' ', '_').lower() or email.split('@')[0]
        username = f"{base_username}_{suffix}"

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': username,
                'bio': f'Google user: {name}',
            }
        )

        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'created': created,
        })

class ProfileView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Users'],
        summary='Public user profile',
        description='Get a public profile for a user including stats and recent match history.',
        parameters=[
            OpenApiParameter(name='username', description='Username', required=True, type=str, location=OpenApiParameter.PATH)
        ],
        responses={
            200: OpenApiResponse(response=ProfileResponseSerializer, description='Profile data'),
            404: OpenApiResponse(response=OpenApiTypes.OBJECT, description='User not found'),
        }
    )
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

        room_ids = [r.id for r in rooms]
        submissions = Submission.objects.filter(
            room_id__in=room_ids, player=user
        ).select_related('room')
        submission_map = {s.room_id: s for s in submissions}

        matches = []
        for room in rooms:
            opponent = room.opponent if room.creator_id == user.id else room.creator
            submission = submission_map.get(room.id)
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


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Auth'],
        summary='Get current user profile',
        description='Retrieve the authenticated user profile information.',
        responses={200: OpenApiResponse(response=UserSerializer)}
    )
    def get(self, request):
        return Response(UserSerializer(request.user).data)

    @extend_schema(
        tags=['Auth'],
        summary='Update current user profile',
        description='Update the authenticated user profile. Supports updating username and bio.',
        request=UserUpdateSerializer,
        responses={
            200: OpenApiResponse(response=UserSerializer, description='Profile updated successfully'),
            400: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Validation error'),
        }
    )
    def patch(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(UserSerializer(request.user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Auth'],
        summary='Logout',
        description='Blacklist the current refresh token, invalidating it. Client should also discard the access token.',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'refresh': {'type': 'string', 'description': 'Refresh token to blacklist'}
                },
                'required': ['refresh']
            }
        },
        responses={
            200: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Logout successful'),
            400: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Refresh token required'),
            401: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Invalid token'),
        }
    )
    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'error': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = OutstandingToken.objects.get(token=refresh_token)
            BlacklistedToken.objects.create(token=token)
            return Response({'message': 'Logout successful'})
        except TokenError:
            return Response({'error': 'Invalid or expired token'}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception:
            return Response({'error': 'Token not found'}, status=status.HTTP_401_UNAUTHORIZED)


class StatsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Users'],
        summary='User statistics',
        description='Get detailed statistics for the authenticated user including ELO, XP, streaks, and win rate.',
        responses={200: OpenApiResponse(response=UserStatsSerializer)}
    )
    def get(self, request):
        user = request.user
        total = user.total_duels
        wins = user.wins
        losses = user.losses
        win_rate = (wins / total * 100) if total > 0 else 0.0

        return Response({
            'total_duels': total,
            'wins': wins,
            'losses': losses,
            'win_rate': round(win_rate, 2),
            'current_streak': user.current_streak,
            'best_streak': user.best_streak,
            'xp': user.xp,
            'level': user.level,
            'elo': user.elo,
            'games_played': user.games_played,
        })


class HistoryView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Users'],
        summary='Duel history',
        description='Get the last 20 finished duels for the authenticated user with results and scores.',
        responses={200: OpenApiResponse(response=MatchHistorySerializer(many=True))}
    )
    def get(self, request):
        user = request.user
        rooms = DuelRoom.objects.select_related('creator', 'opponent').filter(
            Q(creator=user) | Q(opponent=user),
            status='finished'
        ).order_by('-finished_at')[:20]

        room_ids = [r.id for r in rooms]
        submissions = Submission.objects.filter(
            room_id__in=room_ids, player=user
        ).select_related('room')
        submission_map = {s.room_id: s for s in submissions}

        matches = []
        for room in rooms:
            opponent = room.opponent if room.creator_id == user.id else room.creator
            submission = submission_map.get(room.id)
            result = 'win' if submission and submission.is_winner else 'loss'
            score = submission.score if submission else 0.0

            matches.append({
                'code': room.code,
                'opponent': opponent.username if opponent else 'Unknown',
                'result': result,
                'score': score,
                'language': room.language,
                'difficulty': room.difficulty,
                'duration': room.duration if hasattr(room, 'duration') else 180,
                'finished_at': room.finished_at,
            })

        return Response(matches)


class SendFriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Social'],
        summary='Send friend request',
        description='Send a friend request to another user by username.',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'username': {'type': 'string', 'description': 'Username of the user to send request to'}
                },
                'required': ['username']
            }
        },
        responses={
            201: OpenApiResponse(response=FriendRequestSerializer, description='Friend request sent'),
            400: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Invalid request'),
            404: OpenApiResponse(response=OpenApiTypes.OBJECT, description='User not found'),
        }
    )
    def post(self, request):
        username = request.data.get('username')
        if not username:
            return Response({'error': 'Username is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            to_user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        if to_user == request.user:
            return Response({'error': 'Cannot send friend request to yourself'}, status=status.HTTP_400_BAD_REQUEST)

        if request.user.friends.filter(id=to_user.id).exists():
            return Response({'error': 'Already friends'}, status=status.HTTP_400_BAD_REQUEST)

        existing = FriendRequest.objects.filter(from_user=request.user, to_user=to_user).first()
        if existing:
            if existing.status == 'pending':
                return Response({'error': 'Friend request already sent'}, status=status.HTTP_400_BAD_REQUEST)
            elif existing.status == 'declined':
                existing.status = 'pending'
                existing.save()
                serializer = FriendRequestSerializer(existing)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

        friend_request = FriendRequest.objects.create(from_user=request.user, to_user=to_user)
        serializer = FriendRequestSerializer(friend_request)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AcceptFriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Social'],
        summary='Accept friend request',
        description='Accept a pending friend request.',
        parameters=[
            OpenApiParameter(name='request_id', description='Friend request ID', required=True, type=int, location=OpenApiParameter.PATH)
        ],
        responses={
            200: OpenApiResponse(response=FriendRequestSerializer, description='Friend request accepted'),
            404: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Friend request not found'),
        }
    )
    def post(self, request, request_id):
        try:
            friend_request = FriendRequest.objects.get(id=request_id, to_user=request.user, status='pending')
        except FriendRequest.DoesNotExist:
            return Response({'error': 'Friend request not found'}, status=status.HTTP_404_NOT_FOUND)

        friend_request.status = 'accepted'
        friend_request.save()
        request.user.friends.add(friend_request.from_user)
        friend_request.from_user.friends.add(request.user)

        Activity.objects.create(
            user=request.user,
            activity_type='friend_added',
            metadata={'friend_id': friend_request.from_user.id, 'friend_username': friend_request.from_user.username}
        )
        Activity.objects.create(
            user=friend_request.from_user,
            activity_type='friend_added',
            metadata={'friend_id': request.user.id, 'friend_username': request.user.username}
        )

        serializer = FriendRequestSerializer(friend_request)
        return Response(serializer.data)


class DeclineFriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Social'],
        summary='Decline friend request',
        description='Decline a pending friend request.',
        parameters=[
            OpenApiParameter(name='request_id', description='Friend request ID', required=True, type=int, location=OpenApiParameter.PATH)
        ],
        responses={
            200: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Friend request declined'),
            404: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Friend request not found'),
        }
    )
    def post(self, request, request_id):
        try:
            friend_request = FriendRequest.objects.get(id=request_id, to_user=request.user, status='pending')
        except FriendRequest.DoesNotExist:
            return Response({'error': 'Friend request not found'}, status=status.HTTP_404_NOT_FOUND)

        friend_request.status = 'declined'
        friend_request.save()
        return Response({'ok': True})


class FriendListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Social'],
        summary='Friend list',
        description='Get the list of friends for the authenticated user.',
        responses={200: OpenApiResponse(response=FriendSerializer(many=True))}
    )
    def get(self, request):
        friends = request.user.friends.all()
        data = []
        for friend in friends:
            data.append({
                'id': friend.id,
                'username': friend.username,
                'email': friend.email,
                'bio': friend.bio,
                'total_duels': friend.total_duels,
                'wins': friend.wins,
                'losses': friend.losses,
                'xp': friend.xp,
                'level': friend.level,
                'elo': friend.elo,
                'friendship_date': friend.profile.created_at if hasattr(friend, 'profile') else None,
            })
        return Response(data)


class RemoveFriendView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Social'],
        summary='Remove friend',
        description='Remove a friend by user ID.',
        parameters=[
            OpenApiParameter(name='user_id', description='User ID', required=True, type=int, location=OpenApiParameter.PATH)
        ],
        responses={
            200: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Friend removed'),
            404: OpenApiResponse(response=OpenApiTypes.OBJECT, description='User not found or not friends'),
        }
    )
    def delete(self, request, user_id):
        try:
            friend = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        if not request.user.friends.filter(id=friend.id).exists():
            return Response({'error': 'Not friends with this user'}, status=status.HTTP_404_NOT_FOUND)

        request.user.friends.remove(friend)
        friend.friends.remove(request.user)
        return Response({'ok': True})


class ActivityFeedView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Social'],
        summary='Activity feed',
        description='Get the activity feed for the authenticated user and their friends.',
        parameters=[
            OpenApiParameter(name='limit', description='Max activities to return', required=False, type=int),
        ],
        responses={200: OpenApiResponse(response=ActivitySerializer(many=True))}
    )
    def get(self, request):
        limit = int(request.query_params.get('limit', 20))
        friend_ids = request.user.friends.values_list('id', flat=True)
        activities = Activity.objects.filter(
            models.Q(user=request.user) | models.Q(user__in=friend_ids)
        ).select_related('user')[:limit]
        serializer = ActivitySerializer(activities, many=True)
        return Response(serializer.data)
