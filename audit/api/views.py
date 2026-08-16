from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from audit.models import AuditLog
from .serializers import AuditLogSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, OpenApiResponse


class AuditLogListView(generics.ListAPIView):
    """List audit logs (admin only)."""
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdminUser]

    @extend_schema(
        tags=['Audit'],
        summary='List audit logs',
        description='List audit log entries ordered by most recent. Admin only. Supports filtering by user_id, action, and resource_type.',
        parameters=[
            OpenApiParameter(name='user_id', description='Filter by user ID', required=False, type=int),
            OpenApiParameter(name='action', description='Filter by action type', required=False, type=str),
            OpenApiParameter(name='resource_type', description='Filter by resource type', required=False, type=str),
        ],
        responses={200: OpenApiResponse(response=OpenApiTypes.OBJECT)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = AuditLog.objects.select_related('user').all()

        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)

        resource_type = self.request.query_params.get('resource_type')
        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)

        return queryset[:100]


class AuditLogDetailView(generics.RetrieveAPIView):
    """Get a specific audit log entry (admin only)."""
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdminUser]
    queryset = AuditLog.objects.select_related('user').all()

    @extend_schema(
        tags=['Audit'],
        summary='Audit log detail',
        description='Get a specific audit log entry by ID. Admin only.',
        parameters=[
            OpenApiParameter(name='pk', description='Audit log ID', required=True, type=int, location=OpenApiParameter.PATH)
        ],
        responses={
            200: OpenApiResponse(response=AuditLogSerializer),
            404: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Audit log not found'),
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AuditStatsView(generics.GenericAPIView):
    """Get audit statistics (admin only)."""
    permission_classes = [IsAdminUser]

    @extend_schema(
        tags=['Audit'],
        summary='Audit statistics',
        description='Get audit statistics for the last 24 hours and 7 days, plus top resources. Admin only.',
        responses={200: OpenApiResponse(response=OpenApiTypes.OBJECT)}
    )
    def get(self, request):
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Count

        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)

        actions_24h = (
            AuditLog.objects.filter(timestamp__gte=last_24h)
            .values('action')
            .annotate(count=Count('id'))
        )
        actions_7d = (
            AuditLog.objects.filter(timestamp__gte=last_7d)
            .values('action')
            .annotate(count=Count('id'))
        )

        top_resources = (
            AuditLog.objects.filter(timestamp__gte=last_7d)
            .values('resource_type')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )

        return Response({
            'last_24h': {item['action']: item['count'] for item in actions_24h},
            'last_7d': {item['action']: item['count'] for item in actions_7d},
            'top_resources': list(top_resources),
        })
