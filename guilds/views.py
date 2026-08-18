from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from .models import Guild, GuildMember, GuildEvent, GuildEventParticipant, GuildWar
from .serializers import GuildSerializer, GuildCreateSerializer, GuildMemberSerializer, GuildEventSerializer, GuildWarSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, OpenApiResponse

class GuildListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Guilds'],
        summary='List guilds',
        description='Get all public guilds, or all guilds if admin.',
        parameters=[
            OpenApiParameter(name='search', description='Search by name', required=False, type=str),
            OpenApiParameter(name='page', description='Page number', required=False, type=int),
            OpenApiParameter(name='limit', description='Items per page', required=False, type=int),
        ],
        responses={200: OpenApiResponse(response=GuildSerializer(many=True))}
    )
    def get(self, request):
        guilds = Guild.objects.filter(is_public=True)
        search = request.query_params.get('search')
        if search:
            guilds = guilds.filter(name__icontains=search)
        serializer = GuildSerializer(guilds, many=True)
        return Response(serializer.data)

class CreateGuildView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Guilds'],
        summary='Create guild',
        description='Create a new guild. Creator becomes leader.',
        request=GuildCreateSerializer,
        responses={
            201: OpenApiResponse(response=GuildSerializer),
            400: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Validation error'),
        }
    )
    def post(self, request):
        serializer = GuildCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            guild = serializer.save()
            return Response(GuildSerializer(guild).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GuildDetailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Guilds'],
        summary='Guild detail',
        description='Get guild details including members.',
        parameters=[
            OpenApiParameter(name='guild_id', description='Guild ID', required=True, type=int, location=OpenApiParameter.PATH)
        ],
        responses={
            200: OpenApiResponse(response=GuildSerializer),
            404: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Guild not found'),
        }
    )
    def get(self, request, guild_id):
        guild = get_object_or_404(Guild, id=guild_id)
        serializer = GuildSerializer(guild)
        return Response(serializer.data)

class JoinGuildView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Guilds'],
        summary='Join guild',
        description='Join a public guild.',
        parameters=[
            OpenApiParameter(name='guild_id', description='Guild ID', required=True, type=int, location=OpenApiParameter.PATH)
        ],
        responses={
            201: OpenApiResponse(response=GuildMemberSerializer),
            400: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Already a member or guild full'),
            404: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Guild not found'),
        }
    )
    def post(self, request, guild_id):
        guild = get_object_or_404(Guild, id=guild_id)
        if not guild.is_public:
            return Response({'error': 'Guild is private'}, status=status.HTTP_400_BAD_REQUEST)

        existing = GuildMember.objects.filter(guild=guild, user=request.user).first()
        if existing:
            return Response({'error': 'Already a member'}, status=status.HTTP_400_BAD_REQUEST)

        if guild.members.count() >= guild.max_members:
            return Response({'error': 'Guild is full'}, status=status.HTTP_400_BAD_REQUEST)

        member = GuildMember.objects.create(guild=guild, user=request.user, role='member')
        serializer = GuildMemberSerializer(member)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class LeaveGuildView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Guilds'],
        summary='Leave guild',
        description='Leave a guild.',
        parameters=[
            OpenApiParameter(name='guild_id', description='Guild ID', required=True, type=int, location=OpenApiParameter.PATH)
        ],
        responses={
            200: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Left guild'),
            404: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Not a member'),
        }
    )
    def post(self, request, guild_id):
        guild = get_object_or_404(Guild, id=guild_id)
        try:
            member = GuildMember.objects.get(guild=guild, user=request.user)
            member.delete()
            return Response({'ok': True})
        except GuildMember.DoesNotExist:
            return Response({'error': 'Not a member'}, status=status.HTTP_404_NOT_FOUND)

class MyGuildView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Guilds'],
        summary='My guild',
        description='Get the current user guild.',
        responses={200: OpenApiResponse(response=GuildSerializer)}
    )
    def get(self, request):
        member = GuildMember.objects.filter(user=request.user).select_related('guild').first()
        if not member:
            return Response({'error': 'Not in a guild'}, status=status.HTTP_404_NOT_FOUND)
        serializer = GuildSerializer(member.guild)
        return Response(serializer.data)

class GuildEventListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Guilds'],
        summary='Guild events',
        description='Get events for a guild.',
        parameters=[
            OpenApiParameter(name='guild_id', description='Guild ID', required=True, type=int, location=OpenApiParameter.PATH)
        ],
        responses={200: OpenApiResponse(response=GuildEventSerializer(many=True))}
    )
    def get(self, request, guild_id):
        guild = get_object_or_404(Guild, id=guild_id)
        events = GuildEvent.objects.filter(guild=guild)
        serializer = GuildEventSerializer(events, many=True)
        return Response(serializer.data)

class CreateGuildEventView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Guilds'],
        summary='Create guild event',
        description='Create a new event for a guild.',
        parameters=[
            OpenApiParameter(name='guild_id', description='Guild ID', required=True, type=int, location=OpenApiParameter.PATH)
        ],
        request=GuildEventSerializer,
        responses={
            201: OpenApiResponse(response=GuildEventSerializer),
            400: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Validation error'),
        }
    )
    def post(self, request, guild_id):
        guild = get_object_or_404(Guild, id=guild_id)
        member = GuildMember.objects.filter(guild=guild, user=request.user).first()
        if not member or member.role not in ('leader', 'officer'):
            return Response({'error': 'Only leaders and officers can create events'}, status=status.HTTP_403_FORBIDDEN)

        serializer = GuildEventSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(guild=guild, created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GuildWarListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Guilds'],
        summary='Guild wars',
        description='Get guild wars for a guild.',
        parameters=[
            OpenApiParameter(name='guild_id', description='Guild ID', required=True, type=int, location=OpenApiParameter.PATH)
        ],
        responses={200: OpenApiResponse(response=GuildWarSerializer(many=True))}
    )
    def get(self, request, guild_id):
        guild = get_object_or_404(Guild, id=guild_id)
        wars = GuildWar.objects.filter(models.Q(guild1=guild) | models.Q(guild2=guild))
        serializer = GuildWarSerializer(wars, many=True)
        return Response(serializer.data)
