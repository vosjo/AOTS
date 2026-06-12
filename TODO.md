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

**Optional later:**

- Frontend rewrite: unified progress UI across list pages

## Analysis model refactor (planned release)

**Done (dataset → analysis rename):**

- Renamed `DataSet` → `Analysis` (API `/api/analysis/analyses/`, SPA, legacy UI, bulk kind `analyses`)
- **Stufe A.1:** Removed unused `DataTable` model
- **Stufe A.2:** Unified AVG parameter sources on `AverageDataSource` per project (`get_or_create_avg_source`)

**Stufe A.3 — optional, same release or follow-up:**

- Rename `DataSource` → `ParameterSource` (or similar) to distinguish parameter provenance from HDF5 **Analyses**
- Update `Parameter.data_source` FK name / related_name if renamed
- Document: Gaia/catalog rows and AVG are *sources*, not analyses

**Stufe B — larger refactor (backlog, not in initial rename PR):**

- Drop multi-table inheritance: `Analysis` as standalone model (no `DataSource` parent)
- `Parameter`: nullable `analysis` FK for values from HDF5 analyses; separate provenance for external catalogs and averages
- Revisit average/derived-parameter wiring after MTI removal
- Migration path for existing `Parameter.data_source` pointers to analysis rows vs plain sources

**Pre-release check (DataTable):**

```bash
python manage.py shell -c "from analysis.models import DataTable; print('DataTable count:', DataTable.objects.count())"
```

Or SQL: `SELECT COUNT(*) FROM analysis_datatable;` — must be `0` before `DeleteModel('DataTable')`.

## Other

See [docs/api_datatables_contract.md](docs/api_datatables_contract.md) for DataTables API fields.
