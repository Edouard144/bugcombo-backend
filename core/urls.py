from django.contrib import admin
from django.urls import path, include
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

@api_view(['GET'])
def health_check(request):
    import django.db
    health = {
        'status': 'ok',
        'project': 'DebugDuel Backend',
        'version': '1.0.0',
        'checks': {},
    }

    # Database check
    try:
        django.db.connection.ensure_connection()
        health['checks']['database'] = 'ok'
    except Exception as e:
        health['checks']['database'] = f'error: {str(e)}'
        health['status'] = 'degraded'

    # Redis check
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

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check),
    path('api/auth/', include('users.api.urls')),
    path('api/duels/', include('duels.api.urls')),
    path('api/bugs/', include('bugs.api.urls')),
    path('api/chat/', include('chat.api.urls')),
    path('api/notifications/', include('notifications.api.urls')),
    path('api/achievements/', include('achievements.api.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
