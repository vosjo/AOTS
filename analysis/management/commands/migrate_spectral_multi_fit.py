"""Migrate spectral_fit analyses to one multi-fit container per spectrum."""

from django.core.management.base import BaseCommand

from analysis.categories import AnalysisCategory
from analysis.services.multi_fit_migration import migrate_category_containers


class Command(BaseCommand):
    help = 'Merge multiple spectral_fit analyses per spectrum into one multi-fit container.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--project', type=int)

    def handle(self, *args, **options):
        results = migrate_category_containers(
            AnalysisCategory.SPECTRAL_FIT,
            project_id=options.get('project'),
            dry_run=options['dry_run'],
        )
        merged = sum(r.get('merged', 0) for r in results)
        self.stdout.write(self.style.SUCCESS(f'Processed {len(results)} groups, merged {merged} analyses'))
