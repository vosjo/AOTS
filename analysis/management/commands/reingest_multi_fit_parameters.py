"""Re-ingest best-fit parameters for multi-fit containers (e.g. after SED migration)."""

from django.core.management.base import BaseCommand

from analysis.categories import AnalysisCategory
from analysis.models import Analysis
from analysis.services.fit_contribution import reingest_best_fit_parameters
from analysis.services.fit_permissions import category_supports_multi_fit
from analysis.services.fit_sync import sync_fits_from_hdf5


class Command(BaseCommand):
    help = (
        'Re-sync AnalysisFit rows and re-ingest best-fit parameters from HDF5. '
        'Use after migrate_*_multi_fit when DB parameters were incomplete.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--category',
            choices=[
                AnalysisCategory.SED_FIT,
                AnalysisCategory.SPECTRAL_FIT,
                AnalysisCategory.LIGHTCURVE_FIT,
                AnalysisCategory.RV_CURVE,
            ],
            help='Limit to one analysis category',
        )
        parser.add_argument('--project', type=int, help='Limit to project PK')
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        qs = Analysis.objects.exclude(datafile='')
        category = options.get('category')
        if category:
            qs = qs.filter(category=category)
        else:
            qs = qs.filter(category__in=[
                AnalysisCategory.SED_FIT,
                AnalysisCategory.SPECTRAL_FIT,
                AnalysisCategory.LIGHTCURVE_FIT,
                AnalysisCategory.RV_CURVE,
            ])
        project_id = options.get('project')
        if project_id:
            qs = qs.filter(project_id=project_id)

        dry_run = options['dry_run']
        updated = 0
        for analysis in qs.iterator():
            if not category_supports_multi_fit(analysis.category):
                continue
            if dry_run:
                self.stdout.write(f'Would reingest analysis {analysis.pk} ({analysis.category})')
                updated += 1
                continue
            sync_fits_from_hdf5(analysis)
            count = reingest_best_fit_parameters(analysis)
            self.stdout.write(f'Analysis {analysis.pk}: {count} parameters')
            updated += 1

        self.stdout.write(self.style.SUCCESS(f'Done: {updated} analyses'))
