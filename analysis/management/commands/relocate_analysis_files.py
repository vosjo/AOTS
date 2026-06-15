import os

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError

from analysis.models import Analysis


class Command(BaseCommand):
    help = (
        'Move Analysis datafiles from datasets/ to analyses/ and update DB paths '
        '(including simple_history rows). Idempotent.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Log planned moves without changing storage or the database.',
        )
        parser.add_argument(
            '--skip-missing',
            action='store_true',
            help='Skip rows whose file is missing on disk instead of aborting.',
        )
        parser.add_argument(
            '--prune-empty-dirs',
            action='store_true',
            help='Remove empty media/datasets/ after a successful run.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        skip_missing = options['skip_missing']
        HistoricalAnalysis = Analysis.history.model

        moved = 0
        skipped = 0
        missing = 0

        for analysis in Analysis.objects.exclude(datafile='').iterator():
            old_name = analysis.datafile.name
            if not old_name or not old_name.startswith('datasets/'):
                continue

            basename = old_name[len('datasets/'):]
            new_name = self._unique_target_name(basename)

            if not default_storage.exists(old_name):
                msg = f'Analysis pk={analysis.pk}: missing file {old_name}'
                if skip_missing:
                    self.stdout.write(self.style.WARNING(f'Skip: {msg}'))
                    missing += 1
                    continue
                raise CommandError(msg)

            if dry_run:
                self.stdout.write(f'Would move {old_name} -> {new_name} (pk={analysis.pk})')
                moved += 1
                continue

            with default_storage.open(old_name, 'rb') as src:
                default_storage.save(new_name, src)
            default_storage.delete(old_name)

            analysis.datafile.name = new_name
            analysis.save(update_fields=['datafile'])

            HistoricalAnalysis.objects.filter(id=analysis.pk, datafile=old_name).update(
                datafile=new_name,
            )

            self.stdout.write(f'Moved {old_name} -> {new_name} (pk={analysis.pk})')
            moved += 1

        if options['prune_empty_dirs'] and not dry_run:
            datasets_dir = os.path.join(settings.MEDIA_ROOT, 'datasets')
            if os.path.isdir(datasets_dir) and not os.listdir(datasets_dir):
                os.rmdir(datasets_dir)
                self.stdout.write(self.style.SUCCESS('Removed empty media/datasets/'))

        self.stdout.write(
            self.style.SUCCESS(
                f'Done: moved={moved}, skipped_already={skipped}, missing={missing}'
            )
        )

    def _unique_target_name(self, basename):
        candidate = f'analyses/{basename}'
        if not default_storage.exists(candidate):
            return candidate
        stem, ext = os.path.splitext(basename)
        n = 1
        while True:
            candidate = f'analyses/{stem}_{n}{ext}'
            if not default_storage.exists(candidate):
                return candidate
            n += 1
