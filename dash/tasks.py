"""Celery tasks for dashboard plots."""

import logging

from celery import shared_task

logger = logging.getLogger('AOTS.tasks')


@shared_task(bind=True)
def build_starmap_cache_task(self, project_pk, theme='light'):
    from dash.starmap_cache import clear_starmap_build_lock, set_cached_starmap_embed
    from stars.models import Project
    from stars.services.starmap import build_starmap_cache_payload

    project = Project.objects.get(pk=project_pk)
    logger.info(
        'Building starmap cache project=%s theme=%s task_id=%s',
        project_pk,
        theme,
        self.request.id,
    )

    payload = build_starmap_cache_payload(project, theme)
    if payload.get('interactive') is not None:
        set_cached_starmap_embed(project, theme, payload)

    clear_starmap_build_lock(project, theme)
    return {
        'status': 'ready',
        'n_stars_total': payload['n_stars_total'],
        'n_stars_plotted': payload['n_stars_plotted'],
        'downsampled': payload['downsampled'],
        'cached': payload.get('interactive') is not None,
    }
