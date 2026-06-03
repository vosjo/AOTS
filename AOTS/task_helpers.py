"""
Helpers for optional async processing via Celery.
"""


def run_task(task, *args, async_requested=False, **kwargs):
    """
    Run a Celery task synchronously by default to preserve API behaviour.
    """
    if async_requested:
        result = task.delay(*args, **kwargs)
        return None, result.id
    return task(*args, **kwargs), None
