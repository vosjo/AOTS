"""Light-curve time conversions between AOTS storage and ASTRA .astra format."""

from __future__ import annotations

import numpy as np
from astropy.io import fits

# TESS / lightkurve TIME column uses BTJD (BJD - 2457000).
TESS_BTJD_ORIGIN = 2457000.0

# ASTRA TimeScale enum values (see ASTRA src/models/Time.h).
ASTRA_SCALE_JD = 0
ASTRA_SCALE_MJD = 1
ASTRA_SCALE_BJD = 2
ASTRA_SCALE_HJD = 3
ASTRA_SCALE_BTJD = 4
ASTRA_SCALE_BKJD = 5


def is_btjd_native_time(
    time: np.ndarray,
    *,
    telescope: str = '',
    instrument: str = '',
    fits_path: str | None = None,
) -> bool:
    """Return True when FITS TIME values are BTJD/TJD rather than full BJD."""
    telescope_u = (telescope or '').upper()
    instrument_u = (instrument or '').upper()
    if 'TESS' in telescope_u or 'TESS' in instrument_u:
        return True

    if fits_path:
        try:
            hdr = fits.getheader(fits_path, ext=1)
            if (hdr.get('TELESCOP') or '').upper() == 'TESS':
                return True
            creator = (hdr.get('CREATOR') or '').lower()
            if 'lightkurve' in creator and hdr.get('TSTART') is not None:
                return True
            if hdr.get('TSTART') is not None and len(time) and np.nanmedian(time) < 100_000:
                return True
        except Exception:
            pass

    if len(time) == 0:
        return False
    median = float(np.nanmedian(time))
    # BTJD sector times are typically 0–5000; BJD/HJD are millions.
    return median < 100_000 and median >= 0


def astra_native_scale(
    time: np.ndarray,
    *,
    telescope: str = '',
    instrument: str = '',
    fits_path: str | None = None,
) -> int:
    """Return the ASTRA TimeScale byte for a FITS TIME column."""
    values = np.asarray(time, dtype=float)
    if is_btjd_native_time(values, telescope=telescope, instrument=instrument, fits_path=fits_path):
        return ASTRA_SCALE_BTJD
    if len(values) and float(np.nanmedian(values)) > 2_400_000:
        return ASTRA_SCALE_BJD
    if len(values) and 40_000 < float(np.nanmedian(values)) < 100_000:
        return ASTRA_SCALE_MJD
    return ASTRA_SCALE_JD


def native_time_to_bjd(
    time: np.ndarray,
    *,
    telescope: str = '',
    instrument: str = '',
    fits_path: str | None = None,
) -> np.ndarray:
    """Convert AOTS FITS TIME column values to BJD for ASTRA export."""
    values = np.asarray(time, dtype=float)
    if is_btjd_native_time(values, telescope=telescope, instrument=instrument, fits_path=fits_path):
        return values + TESS_BTJD_ORIGIN
    return values


def bjd_to_native_time(bjd: np.ndarray, *, prefer_btjd: bool = True) -> np.ndarray:
    """Convert ASTRA BJD blob values back to AOTS FITS TIME (BTJD for TESS)."""
    values = np.asarray(bjd, dtype=float)
    if len(values) == 0:
        return values
    if prefer_btjd and float(np.nanmedian(values)) > 2_400_000:
        return values - TESS_BTJD_ORIGIN
    return values
