from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from .models import Badge, UserBadge, DailyReward, UserDailyReward, UserStreak
from .serializers import BadgeSerializer, UserBadgeSerializer, DailyRewardSerializer, UserDailyRewardSerializer, UserStreakSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, OpenApiResponse

class BadgeListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Gamification'],
        summary='List badges',
        description='Get all available badges.',
        responses={200: OpenApiResponse(response=BadgeSerializer(many=True))}
    )
    def get(self, request):
        badges = Badge.objects.all()
        serializer = BadgeSerializer(badges, many=True)
        return Response(serializer.data)

class UserBadgesView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Gamification'],
        summary='My badges',
        description='Get all badges unlocked by the authenticated user.',
        responses={200: OpenApiResponse(response=UserBadgeSerializer(many=True))}
    )
    def get(self, request):
        user_badges = UserBadge.objects.filter(user=request.user).select_related('badge')
        serializer = UserBadgeSerializer(user_badges, many=True)
        return Response(serializer.data)

class DailyRewardsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Gamification'],
        summary='Daily rewards',
        description='Get all available daily rewards and user claim history.',
        responses={200: OpenApiResponse(response=OpenApiTypes.OBJECT)}
    )
    def get(self, request):
        rewards = DailyReward.objects.all().order_by('day')
        claimed = UserDailyReward.objects.filter(user=request.user).values_list('day', flat=True)
        return Response({
            'rewards': DailyRewardSerializer(rewards, many=True).data,
            'claimed_days': list(claimed)
        })

    @extend_schema(
        tags=['Gamification'],
        summary='Claim daily reward',
        description='Claim the daily reward for the current day.',
        responses={
            200: OpenApiResponse(response=UserDailyRewardSerializer),
            400: OpenApiResponse(response=OpenApiTypes.OBJECT, description='Already claimed or no reward available'),
        }
    )
    def post(self, request):
        today = timezone.now().date()
        reward = DailyReward.objects.filter(day=today.day).first()
        if not reward:
            return Response({'error': 'No reward available today'}, status=status.HTTP_400_BAD_REQUEST)

        existing = UserDailyReward.objects.filter(user=request.user, day=reward.day).first()
        if existing:
            return Response({'error': 'Already claimed today'}, status=status.HTTP_400_BAD_REQUEST)

        user_reward = UserDailyReward.objects.create(user=request.user, day=reward.day)

        request.user.xp += reward.xp
        request.user.save(update_fields=['xp'])

        streak, _ = UserStreak.objects.get_or_create(user=request.user)
        if streak.last_reward_date and (today - streak.last_reward_date).days == 1:
            streak.current_streak += 1
        elif not streak.last_reward_date or (today - streak.last_reward_date).days > 1:
            streak.current_streak = 1
        streak.longest_streak = max(streak.longest_streak, streak.current_streak)
        streak.last_reward_date = today
        streak.save()

        serializer = UserDailyRewardSerializer(user_reward)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class UserStreakView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Gamification'],
        summary='User streak',
        description='Get the current streak info for the authenticated user.',
        responses={200: OpenApiResponse(response=UserStreakSerializer)}
    )
    def get(self, request):
        streak, _ = UserStreak.objects.get_or_create(user=request.user)
        serializer = UserStreakSerializer(streak)
        return Response(serializer.data)
