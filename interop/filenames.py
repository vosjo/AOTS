"""Safe filenames for interop downloads."""

from __future__ import annotations

import re

_ASTRA_SUFFIX = '.astra'
_MAX_LEN = 255


def sanitize_astra_filename(name: str, *, default: str = 'export.astra') -> str:
    """Return a filesystem-safe `.astra` download name."""
    raw = (name or '').strip()
    if not raw:
        return default
    if raw.lower().endswith(_ASTRA_SUFFIX):
        raw = raw[: -len(_ASTRA_SUFFIX)]
    base = re.sub(r'[^\w.\-+ ]', '_', raw)
    base = re.sub(r'\s+', '_', base).strip('._-')
    if not base:
        return default
    filename = f'{base}{_ASTRA_SUFFIX}'
    return filename[:_MAX_LEN]
