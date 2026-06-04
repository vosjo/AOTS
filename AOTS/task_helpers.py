"""
Helpers for optional async processing via Celery.
"""

from AOTS.task_metadata import store_task_owner


def run_task(task, *args, async_requested=False, owner_user_id=None, project_id=None, **kwargs):
    """
    Run a Celery task synchronously by default to preserve API behaviour.
    """
    if async_requested:
        result = task.delay(*args, **kwargs)
        if owner_user_id is not None:
            store_task_owner(result.id, owner_user_id, project_id=project_id)
        return None, result.id
    return task(*args, **kwargs), None
