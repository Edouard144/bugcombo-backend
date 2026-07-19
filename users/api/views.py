from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.cache import cache
from google.oauth2 import id_token
from google.auth.transport import requests
from .serializers import RegisterSerializer, UserSerializer

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
