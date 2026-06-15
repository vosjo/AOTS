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
- Unified AVG parameter sources on `ParameterSource` with `kind=average` per project (`get_or_create_avg_source`)
- **Stufe A.3:** `DataSource` → `ParameterSource`; `Parameter.parameter_source` replaces `data_source`
- **Stufe B:** `Analysis` is a standalone model (no MTI); HDF5 parameters use `Parameter.analysis`; catalog/AVG parameters use `Parameter.parameter_source`

**Breaking API changes (release):**

- Parameter responses expose `parameter_source` (object with `pk`, `name`) and `analysis` (pk) instead of `data_source`

## Analysis cleanup (architecture)

- [x] **Release 1:** plotting/ingestion services, `calculate_r` fix, project scoping, tests
- [x] **Release 2:** `parameter_averaging` / `parameter_derivation` services, `analysis_history`, `read_analyses` imports
- [x] **Parameter I/O:** domain bookkeeping (AVG sync, derived refresh) via `analysis/services/parameter_io.py` at API, ingestion, star edit, and scripts — not Django signals on `Parameter`/`DerivedParameter`
- [x] **Star I/O:** primary identifier bookkeeping via `stars/services/star_io.py` at API, ingestion, observation upload, and scripts — not Django signals on `Star`
- [x] **Release 3:** PK column `id`, flatten AVG MTI (`ParameterSource.kind`), upload path `analyses/`, `relocate_analysis_files` + `cleanup_orphan_analysis_sources` commands
- [ ] **Release 4:** remove legacy analysis views/templates/JS — gated on [frontend parity checklist](docs/frontend_parity_checklist.md) Analysis section

## Other

See [docs/api_datatables_contract.md](docs/api_datatables_contract.md) for DataTables API fields.
