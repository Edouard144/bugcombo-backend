from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Count
from notifications.models import Notification

User = get_user_model()


class Command(BaseCommand):
    help = 'Send weekly notification digest to active users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print what would be sent without actually sending'
        )

    def handle(self, *args, **options):
        active_users = User.objects.filter(is_active=True, email__isnull=False).exclude(email='')
        sent = 0
        skipped = 0

        for user in active_users:
            unread = Notification.objects.filter(user=user, read=False)
            unread_count = unread.count()

            if unread_count == 0:
                skipped += 1
                continue

            subject = f'BugCombo Weekly Digest: {unread_count} unread notifications'
            message = (
                f'Hi {user.username},\n\n'
                f'You have {unread_count} unread notifications.\n'
                f'Log in to check them out.\n\n'
                f'- BugCombo Team'
            )

            if options['dry_run']:
                self.stdout.write(f'Would send to {user.email}: {subject}')
                sent += 1
            else:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@bugcombo.com'),
                    recipient_list=[user.email],
                    fail_silently=True,
                )
                sent += 1

        self.stdout.write(self.style.SUCCESS(f'Sent {sent} digests, skipped {skipped} users with no notifications'))
