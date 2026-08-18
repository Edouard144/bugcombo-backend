from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Badge, UserBadge, DailyReward, UserDailyReward, UserStreak

User = get_user_model()

class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = ['id', 'name', 'description', 'icon', 'condition_type', 'condition_value']

class UserBadgeSerializer(serializers.ModelSerializer):
    badge = BadgeSerializer(read_only=True)

    class Meta:
        model = UserBadge
        fields = ['id', 'badge', 'unlocked_at']

class DailyRewardSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyReward
        fields = ['id', 'day', 'xp', 'coins', 'description']

class UserDailyRewardSerializer(serializers.ModelSerializer):
    reward = DailyRewardSerializer(read_only=True)

    class Meta:
        model = UserDailyReward
        fields = ['id', 'day', 'reward', 'claimed_at']

class UserStreakSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserStreak
        fields = ['current_streak', 'longest_streak', 'last_reward_date', 'updated_at']
