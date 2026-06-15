from django.core.management.base import BaseCommand
from django.db import connection

from analysis.models import Analysis, Parameter, ParameterSource, ParameterSourceKind


class Command(BaseCommand):
    help = (
        'Delete orphan ParameterSource rows left from the old Analysis MTI parent '
        '(same pk as Analysis, no parameters, not an average source).'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='List rows that would be deleted without deleting.',
        )

    def handle(self, *args, **options):
        if connection.vendor == 'sqlite':
            self.stdout.write(
                self.style.WARNING('Skipping on SQLite (no known orphan rows in dev DBs).')
            )
            return

        analysis_ids = set(Analysis.objects.values_list('pk', flat=True))
        orphans = (
            ParameterSource.objects.filter(pk__in=analysis_ids)
            .exclude(kind=ParameterSourceKind.AVERAGE)
        )

        deleted = 0
        for src in orphans.iterator():
            if Parameter.objects.filter(parameter_source_id=src.pk).exists():
                continue
            if options['dry_run']:
                self.stdout.write(f'Would delete ParameterSource pk={src.pk} name={src.name!r}')
            else:
                src.delete()
            deleted += 1

        verb = 'Would delete' if options['dry_run'] else 'Deleted'
        self.stdout.write(self.style.SUCCESS(f'{verb} {deleted} orphan parameter source(s).'))
