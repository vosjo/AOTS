"""
Store ownership metadata for async Celery tasks (task status API authorization).
"""

from django.core.cache import cache

TASK_OWNER_CACHE_PREFIX = 'aots_task_owner:'
TASK_OWNER_TTL = 60 * 60 * 24  # 24 hours


def store_task_owner(task_id, user_id, project_id=None):
    cache.set(
        f'{TASK_OWNER_CACHE_PREFIX}{task_id}',
        {'user_id': user_id, 'project_id': project_id},
        TASK_OWNER_TTL,
    )


def get_task_owner(task_id):
    return cache.get(f'{TASK_OWNER_CACHE_PREFIX}{task_id}')


def user_may_view_task(user, task_id):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    meta = get_task_owner(task_id)
    if meta is None:
        return False
    return meta.get('user_id') == user.pk
