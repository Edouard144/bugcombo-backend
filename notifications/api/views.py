from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from notifications.models import Notification
from .serializers import NotificationSerializer, NotificationPreferenceSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, OpenApiResponse

class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Notifications'],
        summary='List notifications',
        description='Get all notifications for the authenticated user ordered by most recent first.',
        responses={200: OpenApiResponse(response=NotificationSerializer(many=True))}
    )
    def get(self, request):
        notifications = Notification.objects.filter(user=request.user)
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)

class MarkNotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Notifications'],
        summary='Mark notification as read',
        description='Mark a specific notification as read.',
        parameters=[
            OpenApiParameter(name='pk', description='Notification ID', required=True, type=int, location=OpenApiParameter.PATH)
        ],
        responses={
            200: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Marked as read'),
            404: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Notification not found'),
        }
    )
    def post(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk, user=request.user)
        except Notification.DoesNotExist:
            return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)
        notification.read = True
        notification.save(update_fields=['read'])
        return Response({'ok': True})

class NotificationPreferenceView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Notifications'],
        summary='Notification preferences',
        description='Get or update notification preferences for the authenticated user.',
        responses={
            200: OpenApiResponse(response=NotificationPreferenceSerializer),
            400: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Validation error'),
        }
    )
    def get(self, request):
        try:
            from notifications.models import NotificationPreference
            pref, _ = NotificationPreference.objects.get_or_create(user=request.user)
        except Exception:
            return Response({
                'opponent_joined': True,
                'opponent_submitted': True,
                'duel_judged': True,
                'achievement_unlocked': True,
                'email_notifications': False,
            })
        serializer = NotificationPreferenceSerializer(pref)
        return Response(serializer.data)

    @extend_schema(
        tags=['Notifications'],
        summary='Update notification preferences',
        description='Update notification preferences for the authenticated user.',
        request=NotificationPreferenceSerializer,
        responses={
            200: OpenApiResponse(response=NotificationPreferenceSerializer),
            400: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Validation error'),
        }
    )
    def put(self, request):
        try:
            from notifications.models import NotificationPreference
            pref, _ = NotificationPreference.objects.get_or_create(user=request.user)
        except Exception:
            return Response({'error': 'NotificationPreference model not available'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = NotificationPreferenceSerializer(pref, data=request.data, partial=True)
        if serializer.is_valid():
            for attr, value in serializer.validated_data.items():
                setattr(pref, attr, value)
            pref.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
