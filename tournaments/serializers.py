from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Tournament, TournamentParticipant, TournamentMatch
from users.api.serializers import UserSerializer

User = get_user_model()

class TournamentParticipantSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = TournamentParticipant
        fields = ['id', 'user', 'status', 'seed', 'wins', 'losses', 'created_at']

class TournamentMatchSerializer(serializers.ModelSerializer):
    participant1 = UserSerializer(read_only=True)
    participant2 = UserSerializer(read_only=True)
    winner = UserSerializer(read_only=True)
    loser = UserSerializer(read_only=True)

    class Meta:
        model = TournamentMatch
        fields = ['id', 'round', 'match_number', 'status', 'participant1', 'participant2', 'winner', 'loser', 'score_p1', 'score_p2', 'duel_room', 'created_at']

class TournamentSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    participants = TournamentParticipantSerializer(many=True, read_only=True)
    matches = TournamentMatchSerializer(many=True, read_only=True)
    participant_count = serializers.SerializerMethodField()

    class Meta:
        model = Tournament
        fields = [
            'id', 'name', 'description', 'status', 'format', 'max_participants',
            'min_participants', 'prize_pool', 'registration_start', 'registration_end',
            'start_date', 'end_date', 'creator', 'participants', 'matches',
            'participant_count', 'created_at', 'updated_at'
        ]

    def get_participant_count(self, obj):
        return obj.participants.count()

class TournamentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tournament
        fields = [
            'name', 'description', 'format', 'max_participants', 'min_participants',
            'prize_pool', 'registration_start', 'registration_end', 'start_date'
        ]

    def create(self, validated_data):
        validated_data['creator'] = self.context['request'].user
        return super().create(validated_data)

class BracketMatchSerializer(serializers.ModelSerializer):
    participant1 = UserSerializer(read_only=True)
    participant2 = UserSerializer(read_only=True)
    winner = UserSerializer(read_only=True)

    class Meta:
        model = TournamentMatch
        fields = [
            'id', 'round', 'match_number', 'status', 'participant1', 'participant2',
            'winner', 'loser', 'score_p1', 'score_p2', 'next_match', 'next_match_slot',
            'duel_room', 'created_at'
        ]
