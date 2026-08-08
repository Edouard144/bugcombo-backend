from rest_framework import serializers
from audit.models import AuditLog
from users.api.serializers import UserSerializer


class AuditLogSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'username', 'action', 'resource_type',
            'resource_id', 'ip_address', 'user_agent', 'metadata',
            'timestamp',
        ]
        read_only_fields = fields

    def get_username(self, obj):
        if obj.user:
            return obj.user.username
        return 'system'
