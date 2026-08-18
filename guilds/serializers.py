from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Guild, GuildMember, GuildEvent, GuildEventParticipant, GuildWar

User = get_user_model()

class GuildMemberSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = GuildMember
        fields = ['id', 'user', 'username', 'email', 'role', 'xp', 'joined_at', 'last_active']

class GuildSerializer(serializers.ModelSerializer):
    members = GuildMemberSerializer(many=True, read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Guild
        fields = ['id', 'name', 'tag', 'description', 'icon', 'banner', 'level', 'xp', 'coins', 'max_members', 'is_public', 'creator', 'members', 'member_count', 'created_at', 'updated_at']

    def get_member_count(self, obj):
        return obj.members.count()

class GuildCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guild
        fields = ['name', 'tag', 'description', 'icon', 'banner', 'is_public']

    def create(self, validated_data):
        validated_data['creator'] = self.context['request'].user
        guild = super().create(validated_data)
        GuildMember.objects.create(
            guild=guild,
            user=self.context['request'].user,
            role='leader'
        )
        return guild

class GuildEventSerializer(serializers.ModelSerializer):
    creator = serializers.CharField(source='created_by.username', read_only=True)
    participant_count = serializers.SerializerMethodField()

    class Meta:
        model = GuildEvent
        fields = ['id', 'guild', 'name', 'description', 'event_type', 'start_date', 'end_date', 'max_participants', 'creator', 'participant_count', 'created_at']

    def get_participant_count(self, obj):
        return obj.participants.count()

class GuildWarSerializer(serializers.ModelSerializer):
    guild1_name = serializers.CharField(source='guild1.name', read_only=True)
    guild2_name = serializers.CharField(source='guild2.name', read_only=True)

    class Meta:
        model = GuildWar
        fields = ['id', 'guild1', 'guild1_name', 'guild2', 'guild2_name', 'status', 'start_date', 'end_date', 'guild1_score', 'guild2_score', 'winner', 'created_at']
