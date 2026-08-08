from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models import Notification

def send_notification(user, notification_type, message):
    Notification.objects.create(
        user=user,
        type=notification_type,
        message=message
    )

def send_email_notification(subject, template_name, context, recipient_list):
    if not settings.EMAIL_HOST_USER:
        return
    html_message = render_to_string(template_name, context)
    plain_message = strip_tags(html_message)
    send_mail(
        subject=subject,
        message=plain_message,
        html_message=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list,
        fail_silently=True,
    )

def send_opponent_joined_email(user, opponent_name, room_code):
    send_email_notification(
        subject='Opponent Joined Your Duel!',
        template_name='email/opponent_joined.html',
        context={'user': user, 'opponent_name': opponent_name, 'room_code': room_code},
        recipient_list=[user.email],
    )

def send_duel_judged_email(user, room_code, result):
    send_email_notification(
        subject='Duel Judged',
        template_name='email/duel_judged.html',
        context={'user': user, 'room_code': room_code, 'result': result},
        recipient_list=[user.email],
    )

def send_achievement_unlocked_email(user, achievement_name):
    send_email_notification(
        subject='Achievement Unlocked!',
        template_name='email/achievement_unlocked.html',
        context={'user': user, 'achievement_name': achievement_name},
        recipient_list=[user.email],
    )
