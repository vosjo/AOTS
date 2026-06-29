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
- [x] **Release 4:** remove legacy views/templates/JS — SPA is the only user interface

## Parameter consensus (Konsens-Schicht)

**Done:**

- `ParameterConsensusPolicy` per project (rules: weighted average, preferred source, preferred analysis category, source priority, latest)
- `analysis/services/parameter_consensus.py` — `resolve_consensus`, `get_consensus_parameter`, materialized AVG cache with `consensus_provenance`
- Default policies per project from `consensus_defaults.py` (Gaia source priority, RV/spectral/SED categories, wildcard `*` fallback); seeded on project create + migration 0022
- Project settings UI: `/w/<slug>/settings/consensus/`; API `/api/analysis/consensus-policies/<slug>/`
- Consumers use consensus facade (summary, plotter, HRD, derivation) — not raw `average=True` in application code
- Gaia DR3 import service (`stars/services/gaia_import.py`): photometry + astrometry + derived `mag` / `bp_rp` / `absolute_g_mag` as catalog parameters; SPA buttons + Celery bulk task
- Photometry band registry (`stars/photometry_bands.py`): unified passband definitions; VizieR fetch excludes Gaia (use Gaia DR3 import); SKYMAP U/V/B

**Later:**

- [x] HRD (`dash/plotting.py`): photometry reads removed; axis values via `get_consensus_parameter()` only
- [x] Parameter overview: compact Value column + expandable „Other measurements“
- [ ] Per-star policy overrides (optional)
- [x] Weighted average: inverse-variance mean and combined uncertainty (`parameter_averaging.calculate_average`)

See [docs/architecture.md](docs/architecture.md) for domain models, service layers, and I/O conventions.

## Dashboard Starmap

**Done:**

- Coordinate service (`stars/services/starmap.py`): bulk queries, Aitoff projection, consensus parallax, downsampling
- API: `GET /api/dash/<slug>/starmap/` (cached Bokeh embed + optional `?format=json`); large projects via Celery
- Redis cache + `Project.starmap_cache_version`; interactive Bokeh map with pan/zoom, click → star detail

**Later:**

- [ ] Aladin-lite overlay mode for contextual DSS view around selected star (complement to all-sky Bokeh map)

## Other

See [docs/api_list_contract.md](docs/api_list_contract.md) for REST list API fields.
