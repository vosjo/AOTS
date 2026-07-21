# Analysis HDF5 upload format

User-facing guide (same content as the SPA page at `/w/documentation/#analysis-hdf5`).

Analyses are uploaded from **Analyses → Upload analysis(es)** as HDF5 (`.hdf5` / `.h5`) files.
AOTS matches each file to a star in the current project, detects the category (or uses an upload override), and imports scalar parameters when present.

Prefer the **multi-fit v2** layout for RV, spectral, light-curve, and SED fits. Legacy root `PARAMETERS` / `MODEL` files still work.

## Star matching

1. If root attributes `ra` and `dec` are both non-zero (degrees; sexagesimal strings are accepted), AOTS finds a star in the project within ±0.01° and picks the closest.
2. Otherwise it looks for an exact case-insensitive match on `systemname`. If coordinates are both zero and no matching name exists, upload fails.

Optional root metadata: `name` (analysis title), `note`, `reference` (ADS bibcode).

**ISIS SED** files use group `info/` (`oname`, `jradeg`, `jdedeg`) instead of these root attributes.

## Categories and `type`

| Category | Typical `type` values |
| --- | --- |
| RV curve | `RC`, `RV`, `rv_curve` |
| SED fit | `SF`, `SED`, `sedfit` (or ISIS `info`/`results` layout) |
| Light curve fit | `LC`, `LF`, `lightcurve` |
| Spectral fit | `XF`, `spectral`, `spectral_fit` |
| Cross correlation | `CC`, `cross_corr` |
| Generic | `??`, `GF`, `generic`, `grid` |

## Multi-fit v2 layout (recommended)

```
/
  @type                         # RC | XF | LC | SF | …
  @<category>_format_version    # = 2
  @best_fit_id
  @systemname, @ra, @dec
  @name, @note, @reference      # optional
  DATA/                         # shared observations
  FITS/<fit_id>/
    @isBestFit, @label, @method
    PARAMETERS/
    MODEL/                      # optional
    O-C/                        # optional
```

Format-version attributes: `rv_curve_format_version`, `spectral_fit_format_version`, `lc_fit_format_version`, `sed_fit_format_version` (all `= 2`).

## Legacy single-fit layout

Root `PARAMETERS/`, optionally `DATA/`, `MODEL/`, `O-C/` (no `FITS/` group). Treated as one implicit fit.

## Parameters

Under `PARAMETERS/` (root or `FITS/<id>/PARAMETERS/`): one-row compound dataset with fields `value`, `err_l`, `err_u`, plus attribute `unit`.

Names must be known to AOTS (or aliases). Examples: `p`, `t0`, `e`, `omega`, `k1`/`k2`, `v01`/`v02`, `teff`, `logg`, `rad`, `ebv`, `z`, `L`, `d`.

## DATA, MODEL, and O−C series

Dataset attrs: `xpar`, `ypar`, `datatype` (`discrete` | `continuous`), optional `label`.

Group attrs: `xlabel`, `ylabel`, `xscale`, `yscale`. Use **linear** scales for RV curves. Synthetic photometry (e.g. SED `Iflux`) must stay `discrete`.

`O-C/` is optional and used for residual plots only.

## Notes by category

- **RV curve:** `DATA/measurements` (or any series) with time/phase + `rv` columns; measurements-only files are valid; multiple component series allowed.
- **Spectral / light curve:** observed `DATA/`, model under the fit, parameters in `PARAMETERS/`.
- **SED:** generic AOTS (`type=SF`, `DATA/Obs`, model + discrete synth photometry) or ISIS (`info/`, `results/`, optional `master/sed`).

## Common upload failures

| Message | Meaning |
| --- | --- |
| wrong format / unreadable | Not valid HDF5 |
| basic info unreadable | Missing/invalid root or ISIS `info` attrs |
| no system information present | No usable coordinates and no matching `systemname` |
| No parameters included | Upload OK, but no recognised scalar parameters |
