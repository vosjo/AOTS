# Backlog

## Bulk downloads / uploads (Celery)

**Done:**

- `POST /api/observations/bulk-download/start/` + `GET …/bulk-download/<task_id>/file/`
- Task ownership + Redis cache in production (`CACHE_URL` / broker DB `1`)
- `spectra_list.js`: Celery download when `AOTS_USE_CELERY_BULK_DOWNLOAD=True` (template flag)
- JSZip fallback when flag is `false`
- TTL: `BULK_DOWNLOAD_TTL_SECONDS`, `manage.py cleanup_bulk_downloads`, Celery Beat schedule
- Delete ZIP after successful download when `BULK_DOWNLOAD_DELETE_AFTER_SEND=True`
- Sync download deprecated: `GET api-spec-download/` returns **410** unless `?legacy_sync=1`
- Bulk upload: `POST api-spec-upload/?async=1` enqueues `process_bulk_upload_task`

**Optional later:**

- Wire raw-spec bulk download the same way (`rawspecfiles_list.js`)
- Frontend rewrite: unified progress UI

## Other

See [docs/api_datatables_contract.md](docs/api_datatables_contract.md) for DataTables API fields.
