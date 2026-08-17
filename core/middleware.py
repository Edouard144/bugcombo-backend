import time
import uuid
import logging
import threading

logger = logging.getLogger('core.requests')

_request_stats = {
    'total_requests': 0,
    'total_response_time': 0.0,
}
_lock = threading.Lock()

class RequestLoggingMiddleware:
    """Log every request with method, path, status, duration, and user."""
    def __init__(self, get_response):
        self.get_response = get_response

    async def __call__(self, request):
        request_id = str(uuid.uuid4())[:8]
        request.request_id = request_id
        start = time.time()

        response = await self.get_response(request)

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

    async def __call__(self, request):
        response = await self.get_response(request)
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response

class RequestMetricsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    async def __call__(self, request):
        start = time.time()
        response = await self.get_response(request)
        duration = time.time() - start
        with _lock:
            _request_stats['total_requests'] += 1
            _request_stats['total_response_time'] += duration
        return response

    @classmethod
    def get_stats(cls):
        with _lock:
            total = _request_stats['total_requests']
            avg_time = _request_stats['total_response_time'] / total if total > 0 else 0
            return {
                'total_requests': total,
                'avg_response_time': round(avg_time, 4),
            }

    @classmethod
    def reset(cls):
        with _lock:
            _request_stats['total_requests'] = 0
            _request_stats['total_response_time'] = 0.0
