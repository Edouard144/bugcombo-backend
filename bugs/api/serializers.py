from rest_framework import serializers
from ..models import Bug

class BugListSerializer(serializers.ModelSerializer):
    created_by_username = serializers.SerializerMethodField()

    class Meta:
        model = Bug
        fields = ['id', 'title', 'description', 'language', 'difficulty', 'created_by', 'created_by_username', 'times_used', 'avg_score', 'created_at']
        read_only_fields = ['created_by']

    def get_created_by_username(self, obj):
        return obj.created_by.username

class BugSerializer(serializers.ModelSerializer):
    created_by_username = serializers.SerializerMethodField()

    class Meta:
        model = Bug
        fields = ['id', 'title', 'description', 'language', 'difficulty', 'starter_code', 'test_cases', 'created_by', 'created_by_username', 'times_used', 'avg_score', 'created_at', 'updated_at']
        read_only_fields = ['created_by']

    def get_created_by_username(self, obj):
        return obj.created_by.username
