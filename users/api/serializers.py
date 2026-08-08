from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

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
        fields = ['id', 'username', 'email', 'bio', 'total_duels', 'wins', 'losses', 'created_at']

class MatchHistorySerializer(serializers.Serializer):
    opponent = serializers.CharField()
    result = serializers.CharField()
    score = serializers.FloatField()
    date = serializers.DateTimeField()

class ProfileStatsSerializer(serializers.Serializer):
    wins = serializers.IntegerField()
    losses = serializers.IntegerField()
    total_duels = serializers.IntegerField()
    win_rate = serializers.FloatField()