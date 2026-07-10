"""Backfill SED axis metadata (ylabel/yunit) on existing analysis HDF5 files."""

from django.core.management.base import BaseCommand

from analysis.auxil.sed_hdf5 import ensure_sedfit_axis_metadata
from analysis.categories import AnalysisCategory
from analysis.models import Analysis


class Command(BaseCommand):
    help = 'Add SED axis labels/units to sed_fit HDF5 files that only store bare "flux".'

    def add_arguments(self, parser):
        parser.add_argument(
            '--project',
            type=int,
            help='Limit to analyses in this project id.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Report files that would be updated without writing.',
        )

    def handle(self, *args, **options):
        qs = Analysis.objects.filter(category=AnalysisCategory.SED_FIT).exclude(datafile='')
        if options.get('project'):
            qs = qs.filter(project_id=options['project'])

        updated = 0
        skipped = 0
        for analysis in qs.iterator():
            path = analysis.datafile.path
            if not path:
                skipped += 1
                continue
            if options['dry_run']:
                from analysis.auxil.sed_hdf5 import is_sed_fit_file
                import h5py

                try:
                    with h5py.File(path, 'r') as hdf:
                        if not is_sed_fit_file(hdf):
                            skipped += 1
                            continue
                except OSError:
                    skipped += 1
                    continue
                self.stdout.write(f'would update: {path}')
                updated += 1
                continue

            try:
                if ensure_sedfit_axis_metadata(path):
                    updated += 1
                    self.stdout.write(f'updated: {path}')
                else:
                    skipped += 1
            except OSError as exc:
                self.stderr.write(f'failed {path}: {exc}')
                skipped += 1

        self.stdout.write(self.style.SUCCESS(f'Done: {updated} updated, {skipped} skipped'))
