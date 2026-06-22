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

**SPA:** Star detail → Parameters → *Fetch Gaia DR3*; systems list → select rows → *Fetch Gaia DR3* (Celery bulk, ~5 s between stars).

**API:**

| Endpoint | Behaviour |
| --- | --- |
| `POST /api/systems/stars/<pk>/gaia/fetch/` | Single star (sync) |
| `POST /api/systems/stars/gaia/fetch-bulk/?async=1` | Body `{ "star_ids": [...] }` or `{ "all": true }`; header `Projectid` |

Task status: `GET /api/observations/tasks/<task_id>/` (includes `meta` while `PROGRESS`).

**CLI:** `scripts/update_stars_gaia-dr3.py` wraps the same service (optional skip if DR3 parallax exists).

After a bulk Gaia import, the dashboard starmap reflects updated coordinates on the next load (live Bokeh plot).

### Starmap

Coordinate helpers and metadata live in `stars/services/starmap.py`:

- Aitoff projection in galactic coordinates; parallax from consensus (`get_consensus_parameter`)
- Distance colour when parallax is available; uniform colour fallback when only RA/Dec exist

**Interactive map:** `GET /api/dash/<slug>/starmap/` embeds a Bokeh figure (`interactive` key). Bokeh has no native Aitoff projection; galactic `l,b` are projected server-side with the same transform as matplotlib (`galactic_aitoff_xy`). Star positions as JSON: `?format=json` (`stars` array with `pk`, `ra`, `dec`, `l`, `b`, `distance_kpc`, `url`). PNG export uses Bokeh’s built-in save tool in the plot toolbar. Theme query: `?theme=dark|light`.

## One-time migration notes

After deploying migrations that renamed analysis storage paths (0016–0020), run on staging/production (with media backup):

```
python manage.py relocate_analysis_files
```

Optional on PostgreSQL: `cleanup_orphan_analysis_sources` to remove leftover MTI parent `ParameterSource` rows.
