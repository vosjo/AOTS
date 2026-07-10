"""RV epoch scale detection and ASTRA Time JSON helpers."""

from __future__ import annotations

import numpy as np

# ASTRA Time.h: MJD = JD - 2400000.5; for RV epochs BJD ≈ JD in TDB.
BJD_TO_MJD_OFFSET = 2400000.5

SCALE_BJD = 'BJD'
SCALE_MJD = 'MJD'


def bjd_to_mjd(bjd: float) -> float:
    return float(bjd) - BJD_TO_MJD_OFFSET


def mjd_to_bjd(mjd: float) -> float:
    return float(mjd) + BJD_TO_MJD_OFFSET


def guess_time_scale(
    values: np.ndarray,
    *,
    xpar: str | None = None,
    xlabel: str | None = None,
) -> str:
    """Guess whether RV epochs are stored as BJD or MJD."""
    hints = ' '.join(
        part for part in (xpar or '', xlabel or '') if part
    ).lower()
    if 'mjd' in hints:
        return SCALE_MJD
    if any(token in hints for token in ('bjd', 'hjd', 'jd')):
        return SCALE_BJD

    finite = np.asarray(values, dtype=float)
    finite = finite[np.isfinite(finite)]
    if finite.size == 0:
        return SCALE_BJD
    median = float(np.median(finite))
    if median > 2_400_000.0:
        return SCALE_BJD
    if 40_000.0 < median < 200_000.0:
        return SCALE_MJD
    return SCALE_BJD


def epoch_to_bjd_mjd(epoch: float, scale: str) -> tuple[float, float]:
    if scale == SCALE_MJD:
        mjd = float(epoch)
        return mjd_to_bjd(mjd), mjd
    bjd = float(epoch)
    return bjd, bjd_to_mjd(bjd)


def astra_time_json_from_epoch(
    epoch: float,
    *,
    scale: str | None = None,
    xpar: str | None = None,
    xlabel: str | None = None,
) -> dict[str, float | str]:
    """Build ASTRA Time JSON with consistent BJD and MJD fields."""
    if scale is None:
        scale = guess_time_scale(np.array([epoch]), xpar=xpar, xlabel=xlabel)
    native = float(epoch)
    bjd, mjd = epoch_to_bjd_mjd(native, scale)
    return {
        'scale': scale,
        'val': native,
        'bjd': bjd,
        'mjd': mjd,
    }


def astra_time_json(bjd: float) -> dict[str, float | str]:
    """Legacy helper: epoch is already BJD."""
    return astra_time_json_from_epoch(bjd, scale=SCALE_BJD)
