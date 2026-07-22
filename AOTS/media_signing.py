"""
Short-lived signed URLs for private media downloads.

Access control happens when the URL is issued (authenticated API response).
The download endpoint only verifies signature + expiry (capability model).
"""

from __future__ import annotations

import os
import uuid
from typing import Any

from django.conf import settings
from django.core import signing
from django.urls import reverse

MEDIA_SIGNING_SALT = 'aots.media'


def opaque_upload_to(subdir: str):
    """
    Return an upload_to callable that stores files as ``subdir/<uuid>.<ext>``.

    If the model instance has an empty ``original_name`` attribute, it is set
    from the uploaded basename before the storage path is returned.
    """

    def _upload_to(instance, filename: str) -> str:
        basename = os.path.basename(filename)
        if hasattr(instance, 'original_name') and not getattr(instance, 'original_name', ''):
            instance.original_name = basename[:255]
        _root, ext = os.path.splitext(basename)
        ext = ''.join(c for c in ext.lower() if c.isalnum() or c == '.')[:20]
        return os.path.join(subdir, f'{uuid.uuid4().hex}{ext}')

    return _upload_to


def safe_download_basename(name: str, fallback: str = 'download') -> str:
    """Strip path components and ``..`` for Content-Disposition / ZIP arcnames."""
    base = os.path.basename((name or '').replace('\\', '/').strip())
    if not base or base in {'.', '..'} or '..' in base:
        return fallback
    return base


def sign_media_payload(storage_path: str, original_name: str = '') -> str:
    relative = (storage_path or '').lstrip('/')
    if not relative or '..' in relative.split('/'):
        raise ValueError('Invalid storage path for signing')
    return signing.dumps(
        {'p': relative, 'n': safe_download_basename(original_name, fallback='')},
        salt=MEDIA_SIGNING_SALT,
    )


def unsign_media_token(token: str, max_age: int | None = None) -> dict[str, Any]:
    if max_age is None:
        max_age = getattr(settings, 'MEDIA_SIGNED_URL_MAX_AGE', 900)
    data = signing.loads(token, salt=MEDIA_SIGNING_SALT, max_age=max_age)
    path = (data.get('p') or '').lstrip('/')
    if not path or '..' in path.split('/'):
        raise signing.BadSignature('Invalid path in token')
    return {'p': path, 'n': data.get('n') or ''}


def signed_media_url(storage_path: str, original_name: str = '') -> str:
    """Return a relative URL ``/api/media/<token>/`` for the given storage path."""
    if not storage_path:
        return ''
    token = sign_media_payload(storage_path, original_name=original_name)
    return reverse('api-media-download', kwargs={'token': token})


def signed_filefield_url(field_file, original_name: str = '') -> str:
    """Build a signed download URL from a Django FieldFile."""
    if not field_file or not getattr(field_file, 'name', None):
        return ''
    name = original_name or getattr(field_file.instance, 'original_name', '') or ''
    if not name:
        name = os.path.basename(field_file.name)
    return signed_media_url(field_file.name, original_name=name)
