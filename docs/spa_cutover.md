# SPA frontend

AOTS uses a **Vue SPA** as the only user interface. Django serves the app shell and REST API; there are no legacy page templates.

## URLs

| Path | Handler |
|------|---------|
| `/w/…` | Vue SPA (projects, systems, observations, analysis, dashboard) |
| `/users/…` | Vue SPA (profiles) |
| `/accounts/login`, `/accounts/password_change`, `/accounts/password_reset`, `/accounts/reset/…` | Vue SPA |
| `/admin/…` | Vue SPA (superuser admin UI via `/api/admin/`) |
| `/api/…` | REST API |
| `/django-admin/…` | Django admin (fallback) |

`/app/*` redirects to the same path without the prefix (compatibility for old bookmarks).

## Local development

1. Set `VITE_DEV=True` in `.env`.
2. Terminal 1: `python manage.py runserver`
3. Terminal 2: `cd frontend && npm run dev`
4. Open `http://127.0.0.1:8000/w/projects/`

## Production

1. Set `VITE_DEV=False` in `.env`.
2. Build: `cd frontend && npm ci && npm run build`
3. `python manage.py collectstatic --noinput`
4. Deploy with gunicorn (or your WSGI server).

The shell loads assets from `/static/dist/…` (Vite build output in `site_static/dist/`).
