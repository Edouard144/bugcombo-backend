import logging
from django.core.mail import send_mail
from django.conf import settings
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
    """Send email when user unlocks an achievement."""
    if not user.email:
        return
    subject = f"Achievement Unlocked: {achievement_name}"
    message = (
        f"Hi {user.username},\n\n"
        f"Congratulations! You've unlocked the achievement: {achievement_name}.\n\n"
        f"Keep dueling to earn more!\n\n"
        f"— DebugDuel Team"
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)


def send_duel_judged_email(user, room_code, message_text):
    """Send email after a duel is judged."""
    if not user.email:
        return
    subject = f"Duel {room_code} — Judged!"
    message = (
        f"Hi {user.username},\n\n"
        f"{message_text}\n\n"
        f"View your results at {settings.FRONTEND_URL}/results/{room_code}\n\n"
        f"— DebugDuel Team"
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)
