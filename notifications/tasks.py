from core.celery import app

import logging
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

User = get_user_model()
logger = logging.getLogger(__name__)


@app.task
def send_email_notification(user_id, subject, template_name, context=None):
    context = context or {}
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.error("User %s not found for email notification", user_id)
        return

    if not user.email:
        logger.warning("User %s has no email address", user_id)
        return

    html_message = render_to_string(f'email/{template_name}.html', context)
    send_mail(
        subject=subject,
        message='',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=True,
    )
    logger.info("Sent email to %s: %s", user.email, subject)


@app.task
def send_notification_batch(user_ids, notification_type, message):
    from notifications.models import Notification
    users = User.objects.filter(pk__in=user_ids)
    notifications = [
        Notification(user=user, type=notification_type, message=message) for user in users
    ]
    Notification.objects.bulk_create(notifications, ignore_conflicts=True)
    logger.info("Created %s notifications of type %s", len(notifications), notification_type)


@app.task
def send_duel_judged_notifications(room_code):
    from duels.models import DuelRoom
    from notifications.models import Notification

    try:
        room = DuelRoom.objects.select_related('creator', 'opponent').get(code=room_code)
    except DuelRoom.DoesNotExist:
        return

    notifications = [
        Notification(user=room.creator, type='duel_judged', message=f'Duel {room_code} has been judged'),
        Notification(user=room.opponent, type='duel_judged', message=f'Duel {room_code} has been judged'),
    ]
    Notification.objects.bulk_create(notifications, ignore_conflicts=True)

    if room.creator.email:
        send_email_notification.delay(
            room.creator.pk,
            f'Your duel {room_code} has been judged',
            'duel_judged',
            {'room_code': room_code, 'username': room.creator.username},
        )
    if room.opponent and room.opponent.email:
        send_email_notification.delay(
            room.opponent.pk,
            f'Your duel {room_code} has been judged',
            'duel_judged',
            {'room_code': room_code, 'username': room.opponent.username},
        )
