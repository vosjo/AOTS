"""Redis cache for pre-built dashboard starmap Bokeh embed payloads."""

from __future__ import annotations

from django.conf import settings
from django.core.cache import cache
from django.db.models import F

STARMAP_EMBED_PREFIX = 'starmap:embed:'
STARMAP_BUILD_LOCK_PREFIX = 'starmap:building:'


def _normalized_theme(theme: str | None) -> str:
    return 'light' if theme == 'light' else 'dark'


def starmap_cache_key(project, theme: str | None) -> str:
    theme_name = _normalized_theme(theme)
    return f'{STARMAP_EMBED_PREFIX}{project.pk}:{theme_name}:v{project.starmap_cache_version}'


def starmap_build_lock_key(project, theme: str | None) -> str:
    theme_name = _normalized_theme(theme)
    return f'{STARMAP_BUILD_LOCK_PREFIX}{project.pk}:{theme_name}'


def get_cached_starmap_embed(project, theme: str | None):
    return cache.get(starmap_cache_key(project, theme))


def set_cached_starmap_embed(project, theme: str | None, embed) -> None:
    cache.set(
        starmap_cache_key(project, theme),
        embed,
        getattr(settings, 'STARMAP_CACHE_TTL_SECONDS', 7 * 24 * 3600),
    )


def get_starmap_build_task_id(project, theme: str | None) -> str | None:
    return cache.get(starmap_build_lock_key(project, theme))


def set_starmap_build_task_id(project, theme: str | None, task_id: str) -> None:
    cache.set(
        starmap_build_lock_key(project, theme),
        task_id,
        getattr(settings, 'STARMAP_BUILD_LOCK_TTL_SECONDS', 600),
    )


def clear_starmap_build_lock(project, theme: str | None) -> None:
    cache.delete(starmap_build_lock_key(project, theme))


def invalidate_starmap_cache(project) -> int:
    """
    Bump project cache version and drop embed keys for light/dark themes.
    """
    from stars.models import Project

    Project.objects.filter(pk=project.pk).update(
        starmap_cache_version=F('starmap_cache_version') + 1,
    )
    project.refresh_from_db(fields=['starmap_cache_version'])
    for theme in ('light', 'dark'):
        cache.delete(starmap_cache_key(project, theme))
        cache.delete(starmap_build_lock_key(project, theme))
    return project.starmap_cache_version
