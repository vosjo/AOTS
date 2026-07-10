"""Write ASTRA spectrum blobs as FITS files."""

from __future__ import annotations

import os
import tempfile

import numpy as np
from astropy.io import fits

from interop.blob_pool import BlobReader


def spectrum_arrays(star_spec: dict, reader: BlobReader) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
    wl = np.asarray(reader.get_doubles(star_spec.get('b_wl', -1)), dtype=float)
    flux = np.asarray(reader.get_doubles(star_spec.get('b_flux', -1)), dtype=float)
    err_idx = star_spec.get('b_err', -1)
    err = None
    if err_idx is not None and err_idx >= 0:
        err_arr = reader.get_doubles(err_idx)
        if err_arr:
            err = np.asarray(err_arr, dtype=float)
    return wl, flux, err


def write_spectrum_fits(star_spec: dict, reader: BlobReader, *, output_path: str | None = None) -> str:
    wl, flux, err = spectrum_arrays(star_spec, reader)
    if output_path is None:
        fd, output_path = tempfile.mkstemp(suffix='.fits')
        os.close(fd)

    cols = [fits.Column(name='WAVE', format='D', array=wl), fits.Column(name='FLUX', format='D', array=flux)]
    if err is not None and len(err) == len(wl):
        cols.append(fits.Column(name='ERR', format='D', array=err))
    hdu = fits.BinTableHDU.from_columns(cols)
    hdul = fits.HDUList([fits.PrimaryHDU(), hdu])
    instrument = star_spec.get('instrument') or ''
    if instrument:
        hdul[0].header['INSTRUME'] = instrument
    hdul.writeto(output_path, overwrite=True)
    return output_path
