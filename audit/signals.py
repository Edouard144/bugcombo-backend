import logging
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

logger = logging.getLogger('audit')


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    try:
        from audit.models import AuditLog
        ip = request.META.get('REMOTE_ADDR', '')
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            ip = x_forwarded.split(',')[0].strip()

        AuditLog.objects.create(
            user=user,
            action='LOGIN',
            resource_type='auth',
            resource_id=str(user.pk),
            ip_address=ip,
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            metadata={'method': 'session'},
        )
    except Exception as e:
        logger.exception("Failed to log login: %s", e)


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    try:
        from audit.models import AuditLog
        if user and user.is_authenticated:
            AuditLog.objects.create(
                user=user,
                action='LOGOUT',
                resource_type='auth',
                resource_id=str(user.pk),
            )
    except Exception as e:
        logger.exception("Failed to log logout: %s", e)
