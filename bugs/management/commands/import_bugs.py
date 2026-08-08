import json
from django.core.management.base import BaseCommand
from bugs.models import Bug


class Command(BaseCommand):
    help = 'Import bugs from JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            required=True,
            help='Path to JSON file'
        )
        parser.add_argument(
            '--update',
            action='store_true',
            help='Update existing bugs by ID'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.stderr.write(self.style.ERROR(f'Failed to read file: {e}'))
            return

        if not isinstance(data, list):
            data = [data]

        created = 0
        updated = 0
        skipped = 0

        for item in data:
            try:
                bug_id = item.get('id')
                if bug_id and options['update']:
                    bug, created_flag = Bug.objects.update_or_create(
                        id=bug_id,
                        defaults={
                            'title': item.get('title', ''),
                            'description': item.get('description', ''),
                            'language': item.get('language', 'python'),
                            'difficulty': item.get('difficulty', 'easy'),
                            'starter_code': item.get('starter_code', ''),
                            'test_cases': item.get('test_cases', []),
                            'times_used': item.get('times_used', 0),
                            'avg_score': item.get('avg_score', 0.0),
                        }
                    )
                    if created_flag:
                        created += 1
                    else:
                        updated += 1
                else:
                    Bug.objects.create(
                        title=item.get('title', ''),
                        description=item.get('description', ''),
                        language=item.get('language', 'python'),
                        difficulty=item.get('difficulty', 'easy'),
                        starter_code=item.get('starter_code', ''),
                        test_cases=item.get('test_cases', []),
                        times_used=item.get('times_used', 0),
                        avg_score=item.get('avg_score', 0.0),
                    )
                    created += 1
            except Exception as e:
                skipped += 1
                self.stderr.write(self.style.WARNING(f'Skipped bug: {e}'))

        self.stdout.write(self.style.SUCCESS(f'Imported {created} bugs, updated {updated}, skipped {skipped}'))
