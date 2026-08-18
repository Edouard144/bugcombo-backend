from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from .models import PracticeRoom, PracticeSubmission
from .serializers import PracticeRoomSerializer, PracticeRoomCreateSerializer, PracticeSubmissionSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, OpenApiResponse

class PracticeRoomListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Practice'],
        summary='List practice rooms',
        description='Get all practice rooms for the authenticated user.',
        responses={200: OpenApiResponse(response=PracticeRoomSerializer(many=True))}
    )
    def get(self, request):
        rooms = PracticeRoom.objects.filter(user=request.user)
        serializer = PracticeRoomSerializer(rooms, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=['Practice'],
        summary='Create practice room',
        description='Create a new solo practice room with buggy code.',
        request=PracticeRoomCreateSerializer,
        responses={
            201: OpenApiResponse(response=PracticeRoomSerializer),
            400: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Validation error'),
        }
    )
    def post(self, request):
        serializer = PracticeRoomCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            room = serializer.save()
            room.status = 'in_progress'
            room.started_at = timezone.now()
            room.save()
            return Response(PracticeRoomSerializer(room).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PracticeRoomDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Practice'],
        summary='Practice room detail',
        description='Get details of a practice room.',
        parameters=[
            OpenApiParameter(name='room_id', description='Practice room ID', required=True, type=int, location=OpenApiParameter.PATH)
        ],
        responses={
            200: OpenApiResponse(response=PracticeRoomSerializer),
            404: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Room not found'),
        }
    )
    def get(self, request, room_id):
        room = get_object_or_404(PracticeRoom, id=room_id, user=request.user)
        serializer = PracticeRoomSerializer(room)
        return Response(serializer.data)

class PracticeSubmitView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Practice'],
        summary='Submit practice code',
        description='Submit code for a practice room. Triggers AI judging.',
        parameters=[
            OpenApiParameter(name='room_id', description='Practice room ID', required=True, type=int, location=OpenApiParameter.PATH)
        ],
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'string', 'description': 'Fixed code'}
                },
                'required': ['code']
            }
        },
        responses={
            200: OpenApiResponse(response=PracticeSubmissionSerializer),
            400: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Room not in progress or code empty'),
            404: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Room not found'),
        }
    )
    def post(self, request, room_id):
        room = get_object_or_404(PracticeRoom, id=room_id, user=request.user)
        if room.status != 'in_progress':
            return Response({'error': 'Room is not in progress'}, status=status.HTTP_400_BAD_REQUEST)

        code = request.data.get('code', '').strip()
        if not code:
            return Response({'error': 'Code cannot be empty'}, status=status.HTTP_400_BAD_REQUEST)

        submission = PracticeSubmission.objects.create(room=room, user=request.user, code=code)

        try:
            from duels.judge import judge_submissions
            result = judge_submissions(
                buggy_code=room.buggy_code,
                submission1=code,
                submission2=code,
                language=room.language
            )
            p1 = result['player1']

            submission.correctness = p1['correctness']
            submission.cleanliness = p1['cleanliness']
            submission.efficiency = p1['efficiency']
            submission.security = p1['security']
            submission.score = p1['score']
            submission.ai_feedback = p1['feedback']
            submission.save()

            room.status = 'completed'
            room.score = p1['score']
            room.correctness = p1['correctness']
            room.cleanliness = p1['cleanliness']
            room.efficiency = p1['efficiency']
            room.security = p1['security']
            room.ai_feedback = p1['feedback']
            room.finished_at = timezone.now()
            room.save()

            return Response(PracticeSubmissionSerializer(submission).data)
        except Exception as e:
            return Response({'error': f'Judging failed: {str(e)}'}, status=500)
