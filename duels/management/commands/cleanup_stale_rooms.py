from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from duels.models import DuelRoom


class Command(BaseCommand):
    help = 'Delete stale waiting rooms older than 24 hours'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Age threshold in hours (default: 24)'
        )

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(hours=options['hours'])
        stale_rooms = DuelRoom.objects.filter(status='waiting', created_at__lt=cutoff)
        count = stale_rooms.count()
        stale_rooms.delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {count} stale rooms'))
