# Backlog

## Bulk downloads / uploads (Celery)

**Done:**

- `POST /api/observations/bulk-download/start/` + `GET …/bulk-download/<task_id>/file/`
- Download kinds: `processed`, `raw`, `rawspecfiles`, `lightcurves`, `analyses`
- Task ownership + Redis cache in production (`CACHE_URL` / broker DB `1`)
- List UIs use shared `bulk_download.js` (no browser-side JSZip)
- TTL: `BULK_DOWNLOAD_TTL_SECONDS`, `manage.py cleanup_bulk_downloads`, Celery Beat schedule
- Delete ZIP after successful download when `BULK_DOWNLOAD_DELETE_AFTER_SEND=True`
- Bulk upload: `POST api-spec-upload/?async=1` enqueues `process_bulk_upload_task`

- Frontend rewrite: unified progress UI across list pages (`BulkDownloadProgress.vue` + `useBulkDownload`)

## Analysis model refactor

**Done:**

- Renamed `DataSet` → `Analysis` (API `/api/analysis/analyses/`, SPA, legacy UI, bulk kind `analyses`)
- Removed unused `DataTable` model
- Unified AVG parameter sources on `AverageParameterSource` per project (`get_or_create_avg_source`)
- **Stufe A.3:** `DataSource` → `ParameterSource`, `AverageDataSource` → `AverageParameterSource`; `Parameter.parameter_source` replaces `data_source`
- **Stufe B:** `Analysis` is a standalone model (no MTI); HDF5 parameters use `Parameter.analysis`; catalog/AVG parameters use `Parameter.parameter_source`

**Breaking API changes (release):**

- Parameter responses expose `parameter_source` (object with `pk`, `name`) and `analysis` (pk) instead of `data_source`

## Other

See [docs/api_datatables_contract.md](docs/api_datatables_contract.md) for DataTables API fields.
