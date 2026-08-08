import csv
import json
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from rest_framework.response import Response
from users.api.views import ProfileView

User = get_user_model()


class Command(BaseCommand):
    help = 'Export user data to CSV or JSON'

    def add_arguments(self, parser):
        parser.add_argument(
            '--format',
            type=str,
            choices=['csv', 'json'],
            default='json',
            help='Export format (default: json)'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output file path'
        )

    def handle(self, *args, **options):
        users = User.objects.all()
        rows = []
        for user in users:
            rows.append({
                'id': str(user.id),
                'username': user.username,
                'email': user.email,
                'bio': user.bio,
                'total_duels': user.total_duels,
                'wins': user.wins,
                'losses': user.losses,
                'created_at': user.created_at.isoformat() if user.created_at else '',
                'is_active': user.is_active,
                'last_login': user.last_login.isoformat() if user.last_login else '',
            })

        output_format = options['format']
        output_path = options['output']

        if output_format == 'json':
            content = json.dumps(rows, indent=2)
            if output_path:
                with open(output_path, 'w') as f:
                    f.write(content)
            else:
                self.stdout.write(content)
        elif output_format == 'csv':
            if not rows:
                self.stdout.write('No users to export')
                return
            fieldnames = list(rows[0].keys())
            if output_path:
                with open(output_path, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(rows)
            else:
                writer = csv.DictWriter(self.stdout, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

        self.stdout.write(self.style.SUCCESS(f'Exported {len(rows)} users as {output_format}'))
