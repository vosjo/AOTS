import logging
import time

from celery import shared_task

from stars.services.gaia_import import import_gaia_dr3_for_star

logger = logging.getLogger('AOTS.tasks')

GAIA_BULK_DELAY_SECONDS = 5.0


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
