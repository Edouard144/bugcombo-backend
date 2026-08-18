from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from .models import Replay, ReplayComment
from .serializers import ReplaySerializer, ReplayCreateSerializer, ReplayCommentSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, OpenApiResponse

class ReplayListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Replays'],
        summary='List replays',
        description='Get all public replays, or user replays if authenticated.',
        parameters=[
            OpenApiParameter(name='room_code', description='Filter by room code', required=False, type=str),
            OpenApiParameter(name='user_id', description='Filter by creator user ID', required=False, type=int),
        ],
        responses={200: OpenApiResponse(response=ReplaySerializer(many=True))}
    )
    def get(self, request):
        replays = Replay.objects.filter(is_public=True)
        room_code = request.query_params.get('room_code')
        user_id = request.query_params.get('user_id')
        if room_code:
            replays = replays.filter(duel_room__code=room_code)
        if user_id:
            replays = replays.filter(created_by_id=user_id)
        serializer = ReplaySerializer(replays, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=['Replays'],
        summary='Create replay',
        description='Create a new replay for a duel room.',
        request=ReplayCreateSerializer,
        responses={
            201: OpenApiResponse(response=ReplaySerializer),
            400: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Validation error'),
        }
    )
    def post(self, request):
        serializer = ReplayCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            replay = serializer.save()
            return Response(ReplaySerializer(replay).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ReplayDetailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Replays'],
        summary='Replay detail',
        description='Get a specific replay with comments.',
        parameters=[
            OpenApiParameter(name='replay_id', description='Replay ID', required=True, type=int, location=OpenApiParameter.PATH)
        ],
        responses={
            200: OpenApiResponse(response=ReplaySerializer),
            404: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Replay not found or private'),
        }
    )
    def get(self, request, replay_id):
        replay = get_object_or_404(Replay, id=replay_id)
        if not replay.is_public and replay.created_by != request.user:
            return Response({'error': 'Private replay'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ReplaySerializer(replay)
        return Response(serializer.data)

class ReplayCommentView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Replays'],
        summary='Add comment to replay',
        description='Add a comment to a replay.',
        parameters=[
            OpenApiParameter(name='replay_id', description='Replay ID', required=True, type=int, location=OpenApiParameter.PATH)
        ],
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'text': {'type': 'string', 'description': 'Comment text'}
                },
                'required': ['text']
            }
        },
        responses={
            201: OpenApiResponse(response=ReplayCommentSerializer),
            400: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Empty comment'),
            404: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Replay not found'),
        }
    )
    def post(self, request, replay_id):
        replay = get_object_or_404(Replay, id=replay_id)
        text = request.data.get('text', '').strip()
        if not text:
            return Response({'error': 'Comment cannot be empty'}, status=status.HTTP_400_BAD_REQUEST)
        comment = ReplayComment.objects.create(replay=replay, user=request.user, text=text)
        serializer = ReplayCommentSerializer(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class MyReplaysView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Replays'],
        summary='My replays',
        description='Get all replays created by the authenticated user.',
        responses={200: OpenApiResponse(response=ReplaySerializer(many=True))}
    )
    def get(self, request):
        replays = Replay.objects.filter(created_by=request.user)
        serializer = ReplaySerializer(replays, many=True)
        return Response(serializer.data)
