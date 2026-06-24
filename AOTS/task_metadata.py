"""
Store ownership metadata for async Celery tasks (task status API authorization).
"""

from django.core.cache import cache
from django.utils import timezone

TASK_OWNER_CACHE_PREFIX = 'aots_task_owner:'
TASK_INDEX_KEY = 'aots_task_index'
TASK_OWNER_TTL = 60 * 60 * 24  # 24 hours
TASK_INDEX_MAX = 500


def register_task(task_id, user_id, project_id=None, task_name=None, label=None):
    meta = {
        'user_id': user_id,
        'project_id': project_id,
        'task_name': task_name or '',
        'label': label or '',
        'created_at': timezone.now().isoformat(),
    }
    cache.set(
        f'{TASK_OWNER_CACHE_PREFIX}{task_id}',
        meta,
        TASK_OWNER_TTL,
    )

    index = cache.get(TASK_INDEX_KEY) or []
    if task_id in index:
        index.remove(task_id)
    index.insert(0, task_id)
    cache.set(TASK_INDEX_KEY, index[:TASK_INDEX_MAX], TASK_OWNER_TTL)


def store_task_owner(task_id, user_id, project_id=None):
    register_task(task_id, user_id, project_id=project_id)


def get_task_owner(task_id):
    return cache.get(f'{TASK_OWNER_CACHE_PREFIX}{task_id}')


def list_task_ids():
    return cache.get(TASK_INDEX_KEY) or []


def user_may_view_task(user, task_id):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    meta = get_task_owner(task_id)
    if meta is None:
        return False
    return meta.get('user_id') == user.pk
