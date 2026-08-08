from django.contrib import admin
from django.urls import path, include
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from core.views import MetricsView

@api_view(['GET'])
def health_check(request):
    import django.db
    health = {
        'status': 'ok',
        'project': 'DebugDuel Backend',
        'version': '1.0.0',
        'api_version': 'v1',
        'checks': {},
    }

    try:
        django.db.connection.ensure_connection()
        health['checks']['database'] = 'ok'
    except Exception as e:
        health['checks']['database'] = f'error: {str(e)}'
        health['status'] = 'degraded'

    try:
        from django.core.cache import cache
        cache.set('health_check', 'ok', 10)
        val = cache.get('health_check')
        if val == 'ok':
            health['checks']['redis'] = 'ok'
        else:
            health['checks']['redis'] = 'error: value mismatch'
            health['status'] = 'degraded'
    except Exception as e:
        health['checks']['redis'] = f'error: {str(e)}'

    return Response(health)

api_v1_patterns = [
    path('auth/', include('users.api.urls')),
    path('duels/', include('duels.api.urls')),
    path('bugs/', include('bugs.api.urls')),
    path('chat/', include('chat.api.urls')),
    path('notifications/', include('notifications.api.urls')),
    path('achievements/', include('achievements.api.urls')),
    path('audit/', include('audit.api.urls')),
    path('metrics/', MetricsView.as_view(), name='metrics'),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check),
    path('api/v1/', include(api_v1_patterns)),
    path('api/', include(api_v1_patterns)),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]