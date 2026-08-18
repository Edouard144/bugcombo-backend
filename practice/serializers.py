from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import PracticeRoom, PracticeSubmission

User = get_user_model()

class PracticeSubmissionSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()

    class Meta:
        model = PracticeSubmission
        fields = ['id', 'room', 'user', 'username', 'code', 'submitted_at', 'score', 'correctness', 'cleanliness', 'efficiency', 'security', 'ai_feedback']

    def get_username(self, obj):
        return obj.user.username if obj.user else ''

class PracticeRoomSerializer(serializers.ModelSerializer):
    submissions = PracticeSubmissionSerializer(many=True, read_only=True)

    class Meta:
        model = PracticeRoom
        fields = ['id', 'user', 'language', 'difficulty', 'buggy_code', 'duration', 'status', 'score', 'correctness', 'cleanliness', 'efficiency', 'security', 'ai_feedback', 'started_at', 'finished_at', 'created_at', 'submissions']

class PracticeRoomCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PracticeRoom
        fields = ['language', 'difficulty', 'buggy_code', 'duration']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
