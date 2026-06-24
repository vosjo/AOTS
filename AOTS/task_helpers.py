"""
Helpers for optional async processing via Celery.
"""

import logging

from django.conf import settings

from AOTS.task_metadata import register_task

logger = logging.getLogger('AOTS.tasks')


def run_task(
    task,
    *args,
    async_requested=False,
    owner_user_id=None,
    project_id=None,
    task_name=None,
    label=None,
    **kwargs,
):
    """
    Run a Celery task synchronously by default to preserve API behaviour.
    """
    if not async_requested:
        return task(*args, **kwargs), None

    eager = getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False)
    try:
        if eager:
            logger.debug('Running task %s eagerly (in-process)', task.name)
            async_result = task.apply(args=args, kwargs=kwargs)
        else:
            async_result = task.delay(*args, **kwargs)
    except Exception as exc:
        logger.warning(
            'Async task dispatch failed (%s); running %s synchronously',
            exc,
            task.name,
        )
        async_result = task.apply(args=args, kwargs=kwargs)

    if owner_user_id is not None:
        register_task(
            async_result.id,
            owner_user_id,
            project_id=project_id,
            task_name=task_name or task.name,
            label=label,
        )
    return None, async_result.id
