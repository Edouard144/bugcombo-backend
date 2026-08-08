from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.contrib.auth import get_user_model
from users.api.serializers import UserSerializer

User = get_user_model()


class Command(BaseCommand):
    help = 'Generate and cache leaderboard top players'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Number of top players to cache (default: 10)'
        )
        parser.add_argument(
            '--ttl',
            type=int,
            default=300,
            help='Cache TTL in seconds (default: 300)'
        )

    def handle(self, *args, **options):
        players = User.objects.order_by('-wins', '-total_duels')[:options['limit']]
        data = UserSerializer(players, many=True).data
        cache.set('leaderboard_top10', data, options['ttl'])
        self.stdout.write(self.style.SUCCESS(f'Cached {len(data)} players for {options["ttl"]}s'))
