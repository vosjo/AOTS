# SPA final cutover (Phase 5b)

Parallel beta is the default: classic UI at `/w/…`, new SPA at `/app/w/…`.

## Enable production cutover

1. Deploy with `AOTS_SPA_CUTOVER=true` in environment.
2. Django serves the Vue SPA on `/w/`, `/users/`, `/accounts/login`, etc.
3. `/app/*` redirects to the same path without the prefix.

## After sign-off

1. Remove legacy `site_static/js/*_list.js` and page-specific JS.
2. Remove app templates under `stars/templates/`, `observations/templates/`, etc.
3. Remove `rest_framework_datatables` from `INSTALLED_APPS` and `requirements.txt`.
4. Drop `DualFormatPagination` and `DatatablesOrderingMixin` (REST only).
5. Set Vue Router `base: '/'` (already used when not in beta — verify `vite.config.ts`).

## Rollback

Set `AOTS_SPA_CUTOVER=false` and redeploy; classic templates remain until removed.
