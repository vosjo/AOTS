# AOTS ↔ ASTRA interoperability

## Breaking changes (this release)

- Analysis category `rv_solution` removed; use `rv_curve` for all radial-velocity data.
- RV curve HDF5 files support **v2 multi-fit layout** (`rv_curve_format_version=2`).
- New fields on `Analysis`: `spectrum`, `lightcurve`, `is_best_fit`.
- New API prefix: `/api/interop/`.

## RV curve HDF5 v2

```
/
  type: RC
  rv_curve_format_version: 2
  best_fit_id: <fit-id>
  DATA/measurements/     # time, rv, err_formal, …
  FITS/<fit-id>/
    attrs: isBestFit, method, label
    PARAMETERS/
    MODEL/
```

Legacy single-fit files (root `PARAMETERS` + `MODEL`) remain readable.

Migrate existing files:

```bash
python manage.py migrate_rv_hdf5_layout
```

## ASTRA `.astra` packages

- Magic: `ASTRAPKG`, format version 1.0
- Compressed JSON manifest + binary blob pool
- Import: `POST /api/interop/astra/import/` (field `file`, `project`, optional `star_names`)
- Export: `POST /api/interop/astra/export/` (`star_ids`, export flags)
- Download: `GET /api/interop/astra/export/<task_id>/file/`

## Star matching on import

1. `InteropRecord` ASTRA UUID (re-import)
2. `sourceId` (normalized Gaia id) + position check
3. `tic`, `jname`, `alias` + position
4. Coordinates (2″ tolerance)
5. Create new star

Catalog IDs are stored as AOTS `Identifier` rows; roundtrip IDs use `InteropRecord.external_id`.

## Spectral / LC / SED fits

Multiple ASTRA fits for the same spectrum, light curve, or star are merged into **one container `Analysis`** with contributor fits in HDF5 `FITS/<fit_id>/`. `InteropSubFitRecord` maps ASTRA fit UUIDs to container + fit_id for roundtrip. RV data uses one `rv_curve` analysis per star (multi-fit inside HDF5).

**TESS light curves:** AOTS FITS files store TIME as BTJD (BJD − 2457000). Export writes native `b_val`/`b_scale` plus full BJD in `b_bjd`; import converts back.

**RV curves:** export maps AOTS fit parameters (`k`, `p`, `v0`, `t0`/`t00`, `phi`, …) to ASTRA keys and writes RV times with detected scale (`BJD` or `MJD`) plus both `bjd` and `mjd` fields. Each fit includes `tRefBJD`/`tRefMJD`; `phi` is derived from AOTS `t0` so ASTRA’s displayed T₀ (`getT0BJD()`) matches.

**Photometry / SED:** export supports both ISIS SED HDF5 (`info`/`results/iminimize/CI`/`master/sed`) and AOTS generic `sedfit` files (`DATA/Obs`, `MODEL/tmap`, `PARAMETERS/*`). SED fits export as full `sedModels[]` with parameters, model curve blobs, and observed photometry.

**Deferred ASTRA changes:** see [astra_interop_todo.md](astra_interop_todo.md).
