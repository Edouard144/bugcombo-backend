import json
import logging
from asgiref.sync import sync_to_async

logger = logging.getLogger('audit')


class AuditMiddleware:
    """Log all write operations (POST/PUT/PATCH/DELETE) to the AuditLog model."""

    AUDIT_METHODS = {'POST', 'PUT', 'PATCH', 'DELETE'}

    def __init__(self, get_response):
        self.get_response = get_response

    async def __call__(self, request):
        response = await self.get_response(request)

        if request.method in self.AUDIT_METHODS and request.path.startswith('/api/'):
            await sync_to_sync(self._log_audit)(request, response)

        return response

    def _log_audit(self, request, response):
        try:
            from audit.models import AuditLog

            action = self._get_action(request.method)
            resource_type, resource_id = self._extract_resource(request.path)

            if resource_type in ('health', 'metrics', 'schema', 'docs', 'redoc'):
                return

            user = request.user if hasattr(request, 'user') and request.user.is_authenticated else None
            ip = self._get_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]

            metadata = {}
            if request.method in ('POST', 'PUT', 'PATCH'):
                try:
                    body = json.loads(request.body) if request.body else {}
                    metadata['request_data_keys'] = list(body.keys()) if isinstance(body, dict) else []
                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass

            if response.status_code >= 400:
                metadata['status_code'] = response.status_code

            AuditLog.objects.create(
                user=user,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=ip,
                user_agent=user_agent,
                metadata=metadata,
            )
        except Exception as e:
            logger.exception("Failed to create audit log: %s", e)

    def _get_action(self, method):
        return {
            'POST': 'CREATE',
            'PUT': 'UPDATE',
            'PATCH': 'UPDATE',
            'DELETE': 'DELETE',
        }.get(method, 'UPDATE')

    def _extract_resource(self, path):
        parts = path.strip('/').split('/')
        if len(parts) >= 3:
            resource_type = parts[1] if parts[0] == 'api' else parts[0]
            resource_id = parts[2] if len(parts) > 2 else ''
            if resource_id and resource_id.isdigit():
                return resource_type, resource_id
            elif resource_id and resource_id not in ('create', 'login', 'register', 'me', 'leaderboard', 'featured', 'random', 'clear', 'read', 'health', 'metrics', 'schema', 'docs', 'redoc'):
                return resource_type, resource_id
            return resource_type, ''
        return 'unknown', ''

    def _get_ip(self, request):
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            return x_forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
