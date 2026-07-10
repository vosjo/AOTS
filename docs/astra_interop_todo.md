# ASTRA — open changes for AOTS interoperability

This list collects **proposed but not yet implemented** ASTRA changes identified
during AOTS ↔ ASTRA interoperability debugging. Many symptoms have already been
**mitigated on the AOTS side**; the items here improve robustness and
maintainability in ASTRA itself.

See also: [interoperability.md](interoperability.md)

---

## ASTRA changelog (AOTS-side notes)

Recent ASTRA builds add optional asymmetric fit errors (`*ErrUp`/`*ErrDown`) on RV,
spectral, and LC fits. AOTS export/import maps these to HDF5 `err_l`/`err_u`.
AOTS now exports `tRefBJD`/`tRefMJD` and aligns `phi` from `t0`; ASTRA reads
`tRef*` on import (StarPackage) and preserves it when already set.
Remaining RV phase-plot issues after **DB reload** still need Priority 1 below.

---

### 1. Call `updateFitReferences()` after DB load

- **File:** `src/db/RadialVelocityRepository.cpp` → `loadRadialVelocityCurve()`
- **Change:** After loading points and fits:

  ```cpp
  curve->updateFitReferences();
  ```

- **Problem:** `_tRefBJD` / `_tRefMJD` are set in memory only, not stored in the DB.
  After a project restart or DB reload, `_tRefBJD = 0` → `RVFit::computePhase()`
  falls back to a constant `phi` → all points appear at phase 0 / −1 in the
  folded plot.
- **AOTS workaround:** `phi` is derived from AOTS `t0` on export; that alone is
  not enough when `_tRefBJD` is missing (point phases depend on the reference epoch).
- **Status:** explicitly proposed, not yet implemented

### 2. Persist reference epoch (structural fix)

- **Files:** `src/db/RadialVelocityRepository.cpp`, optionally
  `src/io/StarPackage.cpp` (`rvFitToJson` / `rvFitFromJson`), DB schema `rv_fits`
- **Change:** Store/load `tRefBJD` / `tRefMJD` (or equivalent) in the DB and
  `.astra`, not only at runtime via `updateFitReferences()`.
- **Problem:** More robust than item 1; prevents phase errors permanently.
- **AOTS workaround:** partial, via derived `phi`
- **Status:** mentioned as a long-term alternative

### 3. `Star::setRVCurve()` should set `_RVLoaded = true`

- **File:** `src/models/Star.cpp`
- **Change:** In `setRVCurve()`, set `_RVLoaded = true` after assigning the curve.
- **Problem:** After a `.astra` import, the star has a valid in-memory curve
  (including `tRef`), but `getRVCurve()` reloads from the DB when
  `_RVLoaded == false` and overwrites it — the reference epoch is lost.
- **AOTS workaround:** none
- **Status:** identified during debugging; implicitly relevant for item 1

---

## Priority 2 — RV / time (partially mitigated by AOTS)

### 4. Derive BJD → MJD in `Time`

- **File:** `src/models/Time.cpp` (`propagateOffsets()` or `setBJD()`)
- **Change:** When BJD is set, optionally set `mjd ≈ bjd - 2400000.5` (with clear
  semantics; BJD→MJD is not a pure constant offset without barycentric correction,
  but is often sufficient for table display).
- **Problem:** The MJD column in “RV Points” shows “-” even when BJD is present
  (`getMJD() > 0` fails; `propagateOffsets()` only converts JD ↔ MJD).
- **AOTS workaround:** `mjd` is included in RV export (`interop/rv_export.py`)
- **Status:** root cause analysed; ASTRA fix optional/cleaner

### 5. Imported stars: wire RV loaders after import

- **File:** `src/io/StarShare.cpp` (after `project->addStar(star)`)
- **Change:** For imported stars, set the same `setRVLoader` /
  `setRVCurveFactory` callbacks as in `ApplicationController::openProject()`.
- **Problem:** Imported stars behave differently from stars loaded from the DB
  (lazy load, persist callbacks).
- **AOTS workaround:** none
- **Status:** identified during debugging

---

## Priority 3 — SED / photometry (deliberately deferred)

These changes were **briefly implemented, then reverted on request**. AOTS
instead uses a `sedModels[]` carrier with `observed[]` (see
`interop/export_service.py` → `_photometry_sed_carrier`).

### 6. Dedicated `photometry.sedPoints` field in the `.astra` format

- **File:** `src/io/StarPackage.cpp` (`photometryToJson` / `photometryFromJson`)
- **Change:** Export/import `sedPoints[]` → directly into the canonical SED list
  (`_sedPhotometryPoints`).
- **Problem:** SED Analysis “Photometry Points” does not read `photometry.points`.
- **AOTS workaround:** minimal `sedModels[]` entry with `observed`
- **Status:** reverted; noted for a future ASTRA release

### 7. Fallback in `SEDFitDialog`: `points` → canonical SED points

- **File:** `src/views/tools/SEDFitDialog.cpp` → `ensureCanonicalPhotometryPoints()`
- **Change:** When no SED points / `observed` are present, seed from
  `photometry.points`.
- **Problem:** Helps with older packages without the `sedModels` carrier.
- **AOTS workaround:** `sedModels` carrier
- **Status:** reverted; optional for later

---

## Priority 4 — Interop coordination (not a bug fix)

### 8. Manual AOTS ↔ ASTRA compatibility test

- **Action:** Test AOTS export in ASTRA “Receive Stars…”; maintain a shared
  fixture `.astra` in both repos.
- **Status:** in the implementation plan (Phase 6), still open

### 9. `createdBy: "AOTS"` in the `.astra` manifest

- **File:** `src/io/StarPackage.cpp` / manifest writer
- **Change:** Mark package provenance.
- **Status:** optional, later

### 10. ASTRA periodogram export

- **Status:** deliberately not in `.astra` v1 — “later” in the interop plan

---

## Summary

| # | Topic | Urgency | AOTS workaround? |
|---|--------|---------|------------------|
| 1 | `updateFitReferences()` on RV DB load | high | partial (`phi`) |
| 2 | Persist `tRef` | medium (structural) | partial |
| 3 | `_RVLoaded` in `setRVCurve()` | medium | no |
| 4 | BJD→MJD in `Time` | low | yes (`mjd` export) |
| 5 | RV loaders after import | medium | no |
| 6 | `sedPoints` in StarPackage | low (deferred) | yes (sedModels carrier) |
| 7 | SED fallback from `points` | low (deferred) | yes |
| 8 | Manual interop test | coordination | — |
| 9 | `createdBy` in manifest | optional | — |
| 10 | Periodogram export | later | — |

---

## Recommended order

1. **#1** — one line, biggest benefit for RV phase plot after project reload
2. **#3** — prevents overwriting the imported curve on first `getRVCurve()`
3. **#2** — structurally clean if RV interop should stay stable long term
4. **#5**, **#4** — as needed
5. **#6**, **#7** — if the AOTS `sedModels` carrier should be removed

---

*Last updated: July 2026 (AOTS ↔ ASTRA interoperability debugging)*
