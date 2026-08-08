import time
import uuid
import logging

logger = logging.getLogger('core.requests')


class RequestLoggingMiddleware:
    """Log every request with method, path, status, duration, and user."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = str(uuid.uuid4())[:8]
        request.request_id = request_id
        start = time.time()

        response = self.get_response(request)

        duration = time.time() - start
        user = request.user if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous'
        logger.info(
            "[%s] %s %s → %s (%.3fs) user=%s",
            request_id, request.method, request.path,
            response.status_code, duration, user,
        )
        response['X-Request-ID'] = request_id
        return response


class SecurityHeadersMiddleware:
    """Add security headers to every response."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response
