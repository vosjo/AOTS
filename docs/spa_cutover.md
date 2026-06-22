# SPA final cutover (Phase 5b)

Production deployments use **`AOTS_SPA_CUTOVER=true`** (documented in the [README](../README.md)). The Vue SPA is the only user interface; legacy Django templates are retired at release.

## Enable production cutover

1. Set `AOTS_SPA_CUTOVER=true` and `VITE_DEV=false` in `.env`.
2. Build the frontend (`cd frontend && npm ci && npm run build`) and run `collectstatic`.
3. Django serves the Vue SPA on `/w/`, `/users/`, `/accounts/login`, `/admin/`, etc.
4. `/app/*` redirects to the same path without the prefix (compatibility).

## After sign-off (code cleanup)

1. Remove legacy `site_static/js/*_list.js` and page-specific JS.
2. Remove app templates under `stars/templates/`, `observations/templates/`, etc.
3. Remove `rest_framework_datatables` from `INSTALLED_APPS` and `requirements.txt`.
4. Drop `DualFormatPagination` and `DatatablesOrderingMixin` (REST only).
5. Set Vue Router `base: '/'` (already used when not in beta — verify `vite.config.ts`).

## Rollback

Set `AOTS_SPA_CUTOVER=false` and redeploy; classic templates remain until removed.
