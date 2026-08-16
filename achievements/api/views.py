from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from ..models import Achievement
from .serializers import AchievementSerializer
from drf_spectacular.utils import extend_schema, OpenApiTypes, OpenApiResponse

class UserAchievementsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Achievements'],
        summary='User achievements',
        description='Get all achievements unlocked by the authenticated user.',
        responses={200: OpenApiResponse(response=AchievementSerializer(many=True))}
    )
    def get(self, request):
        achievements = request.user.achievements.all()
        serializer = AchievementSerializer(achievements, many=True)
        return Response(serializer.data)
