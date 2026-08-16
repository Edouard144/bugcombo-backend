from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from duels.models import DuelRoom
from core.middleware import RequestMetricsMiddleware
from drf_spectacular.utils import extend_schema, OpenApiTypes, OpenApiResponse

User = get_user_model()

class MetricsView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Metrics'],
        summary='System metrics',
        description='Get system metrics including active users, duel counts by status, and request statistics.',
        responses={200: OpenApiResponse(response=OpenApiTypes.OBJECT)}
    )
    def get(self, request):
        now = timezone.now()
        active_users = User.objects.filter(last_login__gte=now - timedelta(minutes=15)).count()
        total_duels = DuelRoom.objects.count()
        active_duels = DuelRoom.objects.filter(status='active').count()
        finished_duels = DuelRoom.objects.filter(status='finished').count()
        waiting_duels = DuelRoom.objects.filter(status='waiting').count()

        request_stats = RequestMetricsMiddleware.get_stats()

        return Response({
            'requests': request_stats,
            'active_users': active_users,
            'duels': {
                'total': total_duels,
                'active': active_duels,
                'finished': finished_duels,
                'waiting': waiting_duels,
            },
        })