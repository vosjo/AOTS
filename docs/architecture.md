# AOTS domain architecture

Developer reference for models, services, and data-flow conventions. For installation, Celery/Redis, and day-to-day operations see the [README](../README.md).

## Analysis domain

### Glossary

| Concept | Model | Examples |
| --- | --- | --- |
| HDF5 analysis result | `Analysis` | RV solution, SED fit |
| External / catalog provenance | `ParameterSource` (`kind=catalog`) | Gaia DR3, manual entry |
| Project average container | `ParameterSource` (`kind=average`, `name='AVG'`) | materialized consensus cache row |
| Consensus policy | `ParameterConsensusPolicy` | e.g. parallax from Gaia DR3, teff from SED fit |

Parameters from HDF5 uploads link via `Parameter.analysis`. Catalog and script measurements link via `Parameter.parameter_source`.

### Layering (`analysis` app)

Use-cases live in `analysis/services/`; models hold schema and simple display helpers; `analysis/auxil/` holds stateless HDF5 and plotting I/O.

| Layer | Modules | Responsibility |
| --- | --- | --- |
| API / legacy views | `analysis/api/`, `analysis/views.py` | HTTP, permissions, serialization |
| Services | `analysis_ingestion`, `analysis_plotting`, `analysis_display`, `parameter_io`, `parameter_consensus`, `parameter_averaging`, `parameter_derivation`, `parameter_sources`, `analysis_history`, `analysis_upload` | Upload pipeline, plots, consensus, derived params |
| Models | `Analysis`, `ParameterSource`, `Parameter`, `DerivedParameter`, `ParameterConsensusPolicy` | ORM schema, `__str__`, reference URLs |
| Auxil | `read_analyses`, `plot_analyses`, `plot_parameters`, `fileio` | Pure functions on files and arrays |

### Analysis upload pipeline

`ingest_analysis_file` validates HDF5, matches the star, creates `Parameter` rows, then `create_derived_parameters` when the analysis category defines derived fields.

## Parameter consensus

The **consensus** value shown in summaries, plotters, HRD, and starmaps is resolved by project policy (`analysis/services/parameter_consensus.py`) and stored as a cache row (`Parameter.average=True`, source `AVG`) with `consensus_provenance` describing the winning rule/source.

The `weighted_average` rule combines multiple measurements with an inverse-variance weighted mean (weights `1/σ²`, combined uncertainty `1/√Σ(1/σ²)`); see `analysis/services/parameter_averaging.py`.

New projects receive defaults from `analysis/services/consensus_defaults.py` (Gaia source priority for astrometry, RV/spectral/SED analysis categories for model parameters, wildcard `*` weighted average as fallback). Existing per-project overrides are preserved when seeding.

Configure policies at `/w/<project>/settings/consensus/` (SPA) or via `GET/POST /api/analysis/consensus-policies/<slug>/`.

### I/O conventions

**Writes** go through `analysis/services/parameter_io.py` (create/update/delete measurements, derived records, batch sync). Direct `Parameter.objects.create()` / `.save()` in the Django shell or ad-hoc scripts does **not** sync consensus cache or derived parameters — use `parameter_io` helpers instead.

**Reads** for display/plots should use `get_consensus_parameter()` / `consensus_queryset()` from `parameter_consensus.py`, not `filter(average=True)` in application code. The `average` field marks the materialized cache row only.

## Stars domain

**Writes** that need a primary identifier go through `stars/services/star_io.py` (`create_star`, `save_star`). Direct `Star.save()` in the Django shell does **not** create or update identifiers — use `star_io` helpers instead.

### Photometry band registry

All supported passbands are defined in [`stars/photometry_bands.py`](../stars/photometry_bands.py) (wavelength, zeropoint, CSV column names, VizieR catalog mapping). Consumers (`stars/auxil.py`, `observations/models/photometry.py`, SED plotting) import from this registry.

Supported surveys include Gaia DR3 (manual/CSV only for photometry bands), GALEX, 2MASS, WISE, SKYMAP (U/V/B), APASS, SDSS, and Pan-STARRS.

- **VizieR fetch** (SPA *Fetch from VizieR*): all surveys above **except Gaia** — use *Fetch Gaia DR3* for Gaia photometry and astrometry.
- **Manual / bulk CSV:** all bands including `GAIA3.G`, `GAIA3.BP`, `GAIA3.RP` via columns `phot_g_mean_mag`, etc.
- **API:** `GET /api/systems/stars/<pk>/photometry/options/` returns flat `bands` and grouped `surveys`.

### Gaia DR3 import

Catalog data is fetched from VizieR (`I/355/gaiadr3`) via `stars/services/gaia_import.py`:

- **Photometry:** `GAIA3.G`, `GAIA3.BP`, `GAIA3.RP` in `photometry_set`
- **Parameters** (source `Gaia DR3`): `parallax`, `pmra`, `pmdec`, plus derived `mag`, `bp_rp`, `absolute_g_mag` (stored as catalog parameters for consensus/HRD)

The HRD dashboard (`dash/plotting.py`) reads `mag`, `bp_rp`, and `absolute_g_mag` only via `get_consensus_parameter()` — not from `photometry_set`.

**SPA:** Star detail → Parameters → *Fetch Gaia DR3*; systems list → select rows → *Fetch Gaia DR3* (Celery bulk, ~5 s between stars).

**API:**

| Endpoint | Behaviour |
| --- | --- |
| `POST /api/systems/stars/<pk>/gaia/fetch/` | Single star (sync) |
| `POST /api/systems/stars/gaia/fetch-bulk/?async=1` | Body `{ "star_ids": [...] }` or `{ "all": true }`; header `Projectid` |

Task status: `GET /api/observations/tasks/<task_id>/` (includes `meta` while `PROGRESS`).

**CLI:** `scripts/update_stars_gaia-dr3.py` wraps the same service (optional skip if DR3 parallax exists).

After a bulk Gaia import, the dashboard starmap cache is invalidated; the next load rebuilds the map.

### Starmap

Coordinate helpers and metadata live in `stars/services/starmap.py`:

- Bulk DB queries (stars + consensus parallax) and vectorized galactic/Aitoff projection
- Plot cap via `STARMAP_MAX_POINTS` (default 20 000); metadata includes `n_stars_total`, `n_stars_plotted`, `downsampled`
- Cached Bokeh embed payloads in Redis (`dash/starmap_cache.py`), keyed by project, theme, and `Project.starmap_cache_version`
- Large projects (`STARMAP_SYNC_MAX_STARS`, default 5 000): `GET /api/dash/<slug>/starmap/` returns `202` + `task_id`; Celery task `dash.tasks.build_starmap_cache_task` builds the cache without blocking Gunicorn
- Cache invalidation: star coordinate changes (signal), end of Gaia bulk import

**Interactive map:** `GET /api/dash/<slug>/starmap/` returns `status: ready` with Bokeh `interactive` embed, or `status: pending` while the cache is built. Star positions as JSON: `?format=json`. Theme query: `?theme=dark|light`.

## One-time migration notes

After deploying migrations that renamed analysis storage paths (0016–0020), run on staging/production (with media backup):

```
python manage.py relocate_analysis_files
```

Optional on PostgreSQL: `cleanup_orphan_analysis_sources` to remove leftover MTI parent `ParameterSource` rows.

After the RV consolidation release, migrate legacy RV HDF5 files to the v2 multi-fit layout:

```
python manage.py migrate_rv_hdf5_layout
```

Migration `0027_fix_analysis_id_sequence` restores the PostgreSQL sequence on
`analysis_analysis.id` (lost when the former MTI `datasource_ptr_id` PK became a
standalone column). Without it, new analysis uploads fail with
`null value in column "id" … violates not-null constraint`. Apply via
`python manage.py migrate`.

## Interoperability (`interop` app)

Bidirectional exchange with [ASTRA](https://github.com/schedar/ASTRA) `.astra` star packages. User-facing docs: [`docs/interoperability.md`](interoperability.md).

| Layer | Modules | Responsibility |
| --- | --- | --- |
| API | `interop/api/views.py` | Async import/export Celery tasks, file download |
| Services | `import_service.py`, `export_service.py` | Parse manifest, star matching, create observations/analyses |
| Package I/O | `astra_package.py`, `blob_pool.py` | zlib-compressed manifest + binary blob pool (ASTRAPKG v1.0) |
| Converters | `converters/` | ASTRA JSON ↔ AOTS HDF5/FITS (RV v2, spectral fits, SED, LC) |
| Provenance | `InteropRecord`, `InteropImportBatch` | Stable ASTRA UUIDs for roundtrip |

**Multi-contributor fits (HDF5 v2):** RV, spectral, LC, and SED categories use one container `Analysis` per dataset (star, spectrum, or light curve). Multiple model fits live in `FITS/<fit_id>/` with contributor metadata; DB mirror `AnalysisFit` drives fit-level permissions. Management commands: `migrate_spectral_multi_fit`, `migrate_lc_multi_fit`, `migrate_sed_multi_fit`. Legacy analysis PKs redirect via `AnalysisRedirect` and `GET /api/analysis/analyses/<pk>/redirect/`.

**RV curves:** one `Analysis(rv_curve)` per star; shared `DATA/measurements` plus `FITS/` groups (`analysis/auxil/multi_fit_hdf5.py`, `rv_hdf5.py`). Spectral/LC containers link via `spectrum` / `lightcurve` FKs; best-fit is stored in HDF5 `best_fit_id` and `AnalysisFit.is_best_fit` (not `Analysis.is_best_fit`).

**API:** `POST /api/interop/astra/import/`, `POST /api/interop/astra/export/`, task status via `GET /api/observations/tasks/<task_id>/`.
