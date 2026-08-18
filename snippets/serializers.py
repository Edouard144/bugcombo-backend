from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Snippet, SnippetLike

User = get_user_model()

class SnippetLikeSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = SnippetLike
        fields = ['id', 'user', 'username', 'liked_at']

class SnippetSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(source='created_by.username', read_only=True)
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Snippet
        fields = ['id', 'title', 'description', 'code', 'language', 'is_public', 'created_by', 'likes_count', 'is_liked', 'created_at', 'updated_at']

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return SnippetLike.objects.filter(snippet=obj, user=request.user).exists()
        return False

class SnippetCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Snippet
        fields = ['title', 'description', 'code', 'language', 'is_public']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
