import logging
from django.conf import settings
from django.core.mail import send_mail
from notifications.models import Notification

logger = logging.getLogger(__name__)


def send_notification(user, notification_type, message):
    try:
        Notification.objects.create(
            user=user,
            type=notification_type,
            message=message,
        )
    except Exception:
        logger.exception("Failed to send notification to %s", user)


def send_achievement_unlocked_email(user, achievement_name):
    if not user.email:
        return
    subject = f'Achievement unlocked: {achievement_name}'
    message = f'Congratulations {user.username}! You unlocked the achievement: {achievement_name}'
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@bugcombo.com'),
            recipient_list=[user.email],
            fail_silently=True,
        )
    except Exception:
        logger.exception("Failed to send achievement email to %s", user.email)


def send_duel_judged_email(user, room_code, message):
    if not user.email:
        return
    subject = f'Your duel {room_code} has been judged'
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@bugcombo.com'),
            recipient_list=[user.email],
            fail_silently=True,
        )
    except Exception:
        logger.exception("Failed to send duel judged email to %s", user.email)
