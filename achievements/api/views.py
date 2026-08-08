from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from ..models import Achievement
from .serializers import AchievementSerializer
from notifications.services import send_achievement_unlocked_email

class UserAchievementsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        achievements = request.user.achievements.all()
        serializer = AchievementSerializer(achievements, many=True)
        return Response(serializer.data)
