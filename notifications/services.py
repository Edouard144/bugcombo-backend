import logging
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
