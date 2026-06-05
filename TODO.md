# Backlog

## Bulk downloads / uploads (Celery)

**Done:**

- `POST /api/observations/bulk-download/start/` + `GET …/bulk-download/<task_id>/file/`
- Download kinds: `processed`, `raw`, `rawspecfiles`, `lightcurves`, `datasets`
- Task ownership + Redis cache in production (`CACHE_URL` / broker DB `1`)
- List UIs use shared `bulk_download.js` (no browser-side JSZip)
- TTL: `BULK_DOWNLOAD_TTL_SECONDS`, `manage.py cleanup_bulk_downloads`, Celery Beat schedule
- Delete ZIP after successful download when `BULK_DOWNLOAD_DELETE_AFTER_SEND=True`
- Bulk upload: `POST api-spec-upload/?async=1` enqueues `process_bulk_upload_task`

**Optional later:**

- Frontend rewrite: unified progress UI across list pages

## Other

See [docs/api_datatables_contract.md](docs/api_datatables_contract.md) for DataTables API fields.
