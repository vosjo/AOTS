import logging
import time

from celery import shared_task

from stars.services.gaia_import import import_gaia_dr3_for_star
from observations.services.tess_import import import_tess_lightcurves_for_star, accumulate_tess_bulk_summary

logger = logging.getLogger('AOTS.tasks')

GAIA_BULK_DELAY_SECONDS = 5.0
TESS_BULK_DELAY_SECONDS = 5.0
SIMBAD_BULK_DELAY_SECONDS = 5.0
VIZIER_BULK_DELAY_SECONDS = 5.0


@shared_task(bind=True)
def fetch_gaia_bulk_task(self, project_pk, star_pks, user_pk):
    from stars.models import Project, Star

    project = Project.objects.get(pk=project_pk)
    stars = list(Star.objects.filter(project=project, pk__in=star_pks).order_by('pk'))

    summary = {
        'total': len(stars),
        'ok': 0,
        'no_match': 0,
        'partial': 0,
        'failed': 0,
        'errors': [],
    }

    logger.info(
        'Gaia bulk fetch project=%s stars=%s task_id=%s',
        project_pk,
        len(stars),
        self.request.id,
    )

    for index, star in enumerate(stars, start=1):
        self.update_state(
            state='PROGRESS',
            meta={
                'current': index,
                'total': len(stars),
                'star_name': star.name,
                'star_pk': star.pk,
            },
        )
        try:
            result = import_gaia_dr3_for_star(star)
            if result.status == 'error':
                summary['failed'] += 1
                summary['errors'].append({
                    'star_pk': star.pk,
                    'star_name': star.name,
                    'message': result.message,
                })
            elif result.status == 'no_match':
                summary['no_match'] += 1
            elif result.status == 'partial':
                summary['partial'] += 1
            else:
                summary['ok'] += 1
        except Exception as exc:
            logger.exception('Gaia import failed for star pk=%s', star.pk)
            summary['failed'] += 1
            summary['errors'].append({
                'star_pk': star.pk,
                'star_name': star.name,
                'message': str(exc),
            })

        if index < len(stars):
            time.sleep(GAIA_BULK_DELAY_SECONDS)

    return summary


@shared_task(bind=True)
def fetch_tess_bulk_task(self, project_pk, star_pks, user_pk):
    from stars.models import Project, Star

    project = Project.objects.get(pk=project_pk)
    stars = list(Star.objects.filter(project=project, pk__in=star_pks).order_by('pk'))

    summary = {
        'total': len(stars),
        'ok': 0,
        'no_match': 0,
        'partial': 0,
        'failed': 0,
        'imported_lightcurves': 0,
        'skipped_duplicates': 0,
        'errors': [],
    }

    logger.info(
        'TESS bulk fetch project=%s stars=%s task_id=%s',
        project_pk,
        len(stars),
        self.request.id,
    )

    for index, star in enumerate(stars, start=1):
        self.update_state(
            state='PROGRESS',
            meta={
                'current': index,
                'total': len(stars),
                'star_name': star.name,
                'star_pk': star.pk,
            },
        )
        try:
            result = import_tess_lightcurves_for_star(star)
            accumulate_tess_bulk_summary(summary, star, result)
        except Exception as exc:
            logger.exception('TESS import failed for star pk=%s', star.pk)
            summary['failed'] += 1
            summary['errors'].append({
                'star_pk': star.pk,
                'star_name': star.name,
                'message': str(exc),
            })

        if index < len(stars):
            time.sleep(TESS_BULK_DELAY_SECONDS)

    return summary


@shared_task(bind=True)
def sync_simbad_identifiers_bulk_task(self, project_pk, star_pks, user_pk):
    from stars.models import Project, Star
    from stars.services.simbad_identifiers import (
        accumulate_simbad_bulk_summary,
        sync_simbad_identifiers,
    )

    project = Project.objects.get(pk=project_pk)
    stars = list(Star.objects.filter(project=project, pk__in=star_pks).order_by('pk'))

    summary = {
        'total': len(stars),
        'ok': 0,
        'no_match': 0,
        'partial': 0,
        'failed': 0,
        'added_total': 0,
        'errors': [],
    }

    logger.info(
        'Simbad alias bulk sync project=%s stars=%s task_id=%s',
        project_pk,
        len(stars),
        self.request.id,
    )

    for index, star in enumerate(stars, start=1):
        self.update_state(
            state='PROGRESS',
            meta={
                'current': index,
                'total': len(stars),
                'star_name': star.name,
                'star_pk': star.pk,
            },
        )
        try:
            result = sync_simbad_identifiers(star)
            accumulate_simbad_bulk_summary(summary, star, result)
        except Exception as exc:
            logger.exception('Simbad alias sync failed for star pk=%s', star.pk)
            summary['failed'] += 1
            summary['errors'].append({
                'star_pk': star.pk,
                'star_name': star.name,
                'message': str(exc),
            })

        if index < len(stars):
            time.sleep(SIMBAD_BULK_DELAY_SECONDS)

    return summary


@shared_task(bind=True)
def fetch_vizier_photometry_bulk_task(self, project_pk, star_pks, user_pk):
    from stars.models import Project, Star
    from stars.services.vizier_photometry import (
        accumulate_vizier_bulk_summary,
        import_photometry_from_vizier_for_star,
    )

    project = Project.objects.get(pk=project_pk)
    stars = list(Star.objects.filter(project=project, pk__in=star_pks).order_by('pk'))

    summary = {
        'total': len(stars),
        'ok': 0,
        'no_match': 0,
        'failed': 0,
        'bands_updated_total': 0,
        'errors': [],
    }

    logger.info(
        'VizieR photometry bulk fetch project=%s stars=%s task_id=%s',
        project_pk,
        len(stars),
        self.request.id,
    )

    for index, star in enumerate(stars, start=1):
        self.update_state(
            state='PROGRESS',
            meta={
                'current': index,
                'total': len(stars),
                'star_name': star.name,
                'star_pk': star.pk,
            },
        )
        try:
            result = import_photometry_from_vizier_for_star(star)
            accumulate_vizier_bulk_summary(summary, star, result)
        except Exception as exc:
            logger.exception('VizieR photometry import failed for star pk=%s', star.pk)
            summary['failed'] += 1
            summary['errors'].append({
                'star_pk': star.pk,
                'star_name': star.name,
                'message': str(exc),
            })

        if index < len(stars):
            time.sleep(VIZIER_BULK_DELAY_SECONDS)

    return summary
