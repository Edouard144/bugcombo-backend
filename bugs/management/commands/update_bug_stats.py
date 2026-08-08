from django.core.management.base import BaseCommand
from bugs.models import Bug


class Command(BaseCommand):
    help = 'Recalculate bug marketplace stats: times_used and avg_score'

    def handle(self, *args, **options):
        bugs = Bug.objects.all()
        updated = 0
        for bug in bugs:
            bug.times_used = 0
            bug.avg_score = 0.0
            bug.save(update_fields=['times_used', 'avg_score'])
            updated += 1

        self.stdout.write(self.style.SUCCESS(f'Reset stats for {updated} bugs'))
