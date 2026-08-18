from rest_framework import serializers
from django.contrib.auth import get_user_model
from users.models import FriendRequest, Activity

User = get_user_model()

class AuthResponseSerializer(serializers.Serializer):
    user = serializers.DictField()
    access = serializers.CharField()
    refresh = serializers.CharField()

class TokenRefreshResponseSerializer(serializers.Serializer):
    access = serializers.CharField()

class MatchHistorySerializer(serializers.Serializer):
    code = serializers.CharField()
    opponent = serializers.CharField()
    result = serializers.CharField()
    score = serializers.FloatField()
    language = serializers.CharField()
    difficulty = serializers.CharField()
    finished_at = serializers.DateTimeField()

class ProfileStatsSerializer(serializers.Serializer):
    wins = serializers.IntegerField()
    losses = serializers.IntegerField()
    total_duels = serializers.IntegerField()
    win_rate = serializers.FloatField()

class ProfileResponseSerializer(serializers.Serializer):
    stats = ProfileStatsSerializer()
    matches = MatchHistorySerializer(many=True)

class UserStatsSerializer(serializers.Serializer):
    total_duels = serializers.IntegerField()
    wins = serializers.IntegerField()
    losses = serializers.IntegerField()
    win_rate = serializers.FloatField()
    current_streak = serializers.IntegerField()
    best_streak = serializers.IntegerField()
    xp = serializers.IntegerField()
    level = serializers.IntegerField()
    elo = serializers.IntegerField()
    games_played = serializers.IntegerField()

class SeasonalLeaderboardEntrySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    seasonal_wins = serializers.IntegerField()
    total_duels = serializers.IntegerField()
    current_streak = serializers.IntegerField()
    best_streak = serializers.IntegerField()

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'bio']
        read_only_fields = ['email']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'bio', 'total_duels', 'wins', 'losses',
            'current_streak', 'best_streak', 'last_win_at', 'created_at',
            'xp', 'level', 'elo', 'games_played'
        ]

class FriendRequestSerializer(serializers.ModelSerializer):
    from_user = UserSerializer(read_only=True)
    to_user = UserSerializer(read_only=True)

    class Meta:
        model = FriendRequest
        fields = ['id', 'from_user', 'to_user', 'status', 'created_at', 'updated_at']

class ActivitySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Activity
        fields = ['id', 'user', 'activity_type', 'metadata', 'created_at']

class FriendSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()
    bio = serializers.CharField()
    total_duels = serializers.IntegerField()
    wins = serializers.IntegerField()
    losses = serializers.IntegerField()
    xp = serializers.IntegerField()
    level = serializers.IntegerField()
    elo = serializers.IntegerField()
    friendship_date = serializers.DateTimeField()
