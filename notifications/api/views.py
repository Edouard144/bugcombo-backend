from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from notifications.models import Notification
from .serializers import NotificationSerializer, NotificationPreferenceSerializer

class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(user=request.user)
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)

class MarkNotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

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

    def get(self, request):
        try:
            from notifications.models import NotificationPreference
            pref, _ = NotificationPreference.objects.get_or_create(user=request.user)
        except Exception:
            return Response({
                'email_opponent_joined': True,
                'email_duel_judged': True,
                'email_achievement_unlocked': True,
                'push_notifications': True,
            })
        serializer = NotificationPreferenceSerializer(pref)
        return Response(serializer.data)

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
