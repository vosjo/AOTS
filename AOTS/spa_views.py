import json
from pathlib import Path

from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.middleware.csrf import get_token
from django.shortcuts import render
from django.views.decorators.cache import never_cache


def _manifest_candidates() -> list[Path]:
    base = Path(settings.BASE_DIR) / 'site_static' / 'dist'
    return [
        base / '.vite' / 'manifest.json',
        base / 'manifest.json',
    ]


def _load_vite_manifest() -> dict:
    for path in _manifest_candidates():
        if path.is_file():
            with path.open(encoding='utf-8') as fh:
                return json.load(fh)
    return {}


def vite_entry_assets() -> dict[str, list[str] | str | None]:
    """Resolve hashed JS/CSS URLs for the SPA entry from Vite's manifest."""
    manifest = _load_vite_manifest()
    entry = manifest.get('index.html') or manifest.get('src/main.ts')
    if not entry:
        # Fallback for builds without a manifest (legacy stable filenames).
        return {
            'js': staticfiles_storage.url('dist/assets/index.js'),
            'css': [staticfiles_storage.url('dist/assets/index.css')],
        }

    js_file = entry.get('file')
    css_files = entry.get('css') or []
    return {
        'js': staticfiles_storage.url(f'dist/{js_file}') if js_file else None,
        'css': [staticfiles_storage.url(f'dist/{name}') for name in css_files],
    }


@never_cache
def spa_index(request, *args, **kwargs):
    assets = vite_entry_assets()
    return render(request, 'spa/index.html', {
        'csrf_token': get_token(request),
        'vite_dev': getattr(settings, 'VITE_DEV', False),
        'test_installation': getattr(settings, 'AOTS_TEST_INSTALLATION', False),
        'router_base': '/',
        'vite_js': assets['js'],
        'vite_css': assets['css'],
    })
