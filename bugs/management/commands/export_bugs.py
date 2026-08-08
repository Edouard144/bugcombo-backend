import csv
import json
from django.core.management.base import BaseCommand
from bugs.models import Bug


class Command(BaseCommand):
    help = 'Export bugs to JSON or CSV'

    def add_arguments(self, parser):
        parser.add_argument(
            '--format',
            type=str,
            choices=['json', 'csv'],
            default='json',
            help='Export format (default: json)'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output file path'
        )

    def handle(self, *args, **options):
        bugs = Bug.objects.all()
        rows = []
        for bug in bugs:
            rows.append({
                'id': str(bug.id),
                'title': bug.title,
                'description': bug.description,
                'language': bug.language,
                'difficulty': bug.difficulty,
                'starter_code': bug.starter_code,
                'test_cases': json.dumps(bug.test_cases) if bug.test_cases else '[]',
                'created_by': str(bug.created_by_id),
                'times_used': bug.times_used,
                'avg_score': bug.avg_score,
                'created_at': bug.created_at.isoformat() if bug.created_at else '',
                'updated_at': bug.updated_at.isoformat() if bug.updated_at else '',
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
                self.stdout.write('No bugs to export')
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

        self.stdout.write(self.style.SUCCESS(f'Exported {len(rows)} bugs as {output_format}'))
