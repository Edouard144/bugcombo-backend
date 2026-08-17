from rest_framework import serializers
from duels.models import DuelRoom, Submission
from users.api.serializers import UserSerializer

class SubmissionSerializer(serializers.ModelSerializer):
    player = UserSerializer(read_only=True)
    username = serializers.SerializerMethodField()

    class Meta:
        model = Submission
        fields = ['id', 'room', 'player', 'username', 'code', 'submitted_at', 'score', 'correctness', 'cleanliness', 'efficiency', 'security', 'ai_feedback', 'is_winner']

    def get_username(self, obj):
        if obj.player:
            return obj.player.username
        return ''

class DetailedSubmissionSerializer(serializers.ModelSerializer):
    player = UserSerializer(read_only=True)
    username = serializers.SerializerMethodField()

    class Meta:
        model = Submission
        fields = [
            'id', 'player', 'username', 'code', 'submitted_at',
            'score', 'correctness', 'cleanliness', 'efficiency', 'security',
            'ai_feedback', 'is_winner',
        ]

    def get_username(self, obj):
        if obj.player:
            return obj.player.username
        return ''

class DuelRoomSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    opponent = UserSerializer(read_only=True)

    class Meta:
        model = DuelRoom
        fields = ['id', 'code', 'creator', 'opponent', 'status', 'language', 'difficulty', 'duration', 'buggy_code', 'started_at', 'finished_at', 'created_at']

class MatchDetailSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    opponent = UserSerializer(read_only=True)
    submissions = serializers.SerializerMethodField()
    winner = serializers.SerializerMethodField()
    duration_taken = serializers.SerializerMethodField()

    class Meta:
        model = DuelRoom
        fields = [
            'id', 'code', 'creator', 'opponent', 'status', 'language',
            'difficulty', 'duration', 'buggy_code', 'started_at', 'finished_at',
            'created_at', 'submissions', 'winner', 'duration_taken',
        ]

    def get_submissions(self, obj):
        subs = Submission.objects.filter(room=obj).select_related('player')
        return DetailedSubmissionSerializer(subs, many=True).data

    def get_winner(self, obj):
        winner_sub = Submission.objects.filter(room=obj, is_winner=True).select_related('player').first()
        if winner_sub:
            return {
                'username': winner_sub.player.username,
                'score': winner_sub.score,
            }
        if obj.status == 'finished':
            return {'username': None, 'score': None, 'tie': True}
        return None

    def get_duration_taken(self, obj):
        if obj.started_at and obj.finished_at:
            delta = obj.finished_at - obj.started_at
            return int(delta.total_seconds())
        return None

class DuelRecentMatchSerializer(serializers.Serializer):
    code = serializers.CharField()
    opponent = serializers.CharField()
    result = serializers.CharField()
    score = serializers.FloatField()
    language = serializers.CharField()
    difficulty = serializers.CharField()
    finished_at = serializers.DateTimeField()

class DuelStatsSerializer(serializers.Serializer):
    total_duels = serializers.IntegerField()
    wins = serializers.IntegerField()
    losses = serializers.IntegerField()
    win_rate = serializers.FloatField()
    current_streak = serializers.IntegerField()
    best_streak = serializers.IntegerField()
    recent_matches = DuelRecentMatchSerializer(many=True)
