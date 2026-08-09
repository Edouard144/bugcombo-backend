from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed default achievements'

    def handle(self, *args, **options):
        self.stdout.write('Seeding achievements is handled by the achievements app.')
        self.stdout.write('Run this after the achievements app is installed.')
        self.stdout.write(self.style.SUCCESS('Achievement seed command ready'))
