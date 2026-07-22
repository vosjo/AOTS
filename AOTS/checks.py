"""Production security system checks."""

from django.core.checks import Warning, register


def _redis_url_has_password(url: str) -> bool:
    if not url or not url.startswith('redis'):
        return True
    # redis://:password@host or redis://user:password@host
    try:
        after_scheme = url.split('://', 1)[1]
        authority = after_scheme.split('/', 1)[0]
        if '@' not in authority:
            return False
        userinfo = authority.rsplit('@', 1)[0]
        return ':' in userinfo and bool(userinfo.split(':', 1)[1])
    except Exception:
        return False


@register()
def check_redis_auth(app_configs, **kwargs):
    from django.conf import settings as dj_settings

    if getattr(dj_settings, 'DEBUG', True):
        return []

    errors = []
    for name in ('CELERY_BROKER_URL', 'CACHE_URL'):
        url = getattr(dj_settings, name, '') or ''
        if name == 'CACHE_URL' and not url:
            caches = getattr(dj_settings, 'CACHES', {})
            url = (caches.get('default') or {}).get('LOCATION', '')
        if url.startswith('redis') and not _redis_url_has_password(url):
            errors.append(
                Warning(
                    f'{name} Redis URL has no password.',
                    hint='Use redis://:password@host:6379/N in production.',
                    id='aots.W001',
                )
            )
    return errors
