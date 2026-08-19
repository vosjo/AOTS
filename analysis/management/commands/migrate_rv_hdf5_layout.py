"""Migrate legacy RV HDF5 files to v2 multi-fit layout."""

import os
import shutil
import tempfile

from django.core.management.base import BaseCommand

from analysis.auxil.fileio import read2dict
from analysis.auxil.rv_hdf5 import is_rv_curve_v2, write_migrated_v2_file
from analysis.categories import AnalysisCategory
from analysis.models import Analysis


class Command(BaseCommand):
    help = 'Convert legacy RV curve / RV solution HDF5 files to v2 multi-fit layout.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Report only, do not modify files')
        parser.add_argument('--project', type=int, help='Limit to project PK')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        project_id = options.get('project')

        qs = Analysis.objects.filter(category=AnalysisCategory.RV_CURVE).exclude(datafile='')
        if project_id:
            qs = qs.filter(project_id=project_id)

        converted = 0
        skipped = 0
        failed = []

        for analysis in qs.iterator():
            path = analysis.datafile.path
            if not os.path.isfile(path):
                failed.append((analysis.pk, 'missing file'))
                continue
            try:
                data = read2dict(path)
            except Exception as exc:
                failed.append((analysis.pk, str(exc)))
                continue

            if is_rv_curve_v2(data):
                skipped += 1
                continue

            if dry_run:
                self.stdout.write(f'Would convert analysis {analysis.pk}: {path}')
                converted += 1
                continue

            try:
                with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as tmp:
                    tmp_path = tmp.name
                if write_migrated_v2_file(path, tmp_path):
                    shutil.move(tmp_path, path)
                    converted += 1
                    self.stdout.write(self.style.SUCCESS(f'Converted analysis {analysis.pk}'))
                else:
                    os.unlink(tmp_path)
                    failed.append((analysis.pk, 'migration produced no v2 output'))
            except Exception as exc:
                failed.append((analysis.pk, str(exc)))

        self.stdout.write(
            f'Done: converted={converted}, skipped={skipped}, failed={len(failed)}'
        )
        for pk, reason in failed:
            self.stdout.write(self.style.WARNING(f'  analysis {pk}: {reason}'))
