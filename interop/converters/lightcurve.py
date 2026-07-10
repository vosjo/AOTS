"""Convert ASTRA lightcurve blobs to FITS."""

from __future__ import annotations

import os
import tempfile

import numpy as np
from astropy.io import fits

from interop.lc_time import bjd_to_native_time


def write_lightcurve_fits(lc_obj: dict, reader: BlobReader, *, output_path: str | None = None) -> str:
    bjd = np.asarray(reader.get_doubles(lc_obj.get('b_bjd', -1)), dtype=float)
    flux = np.asarray(reader.get_doubles(lc_obj.get('b_flux', -1)), dtype=float)
    ferr = np.asarray(reader.get_doubles(lc_obj.get('b_ferr', -1)), dtype=float)
    if output_path is None:
        fd, output_path = tempfile.mkstemp(suffix='.fits')
        os.close(fd)

    if len(bjd):
        time = bjd_to_native_time(bjd)
    else:
        time = np.asarray(reader.get_doubles(lc_obj.get('b_val', -1)), dtype=float)
    cols = [
        fits.Column(name='TIME', format='D', array=time),
        fits.Column(name='PDCSAP_FLUX', format='D', array=flux),
    ]
    if len(ferr) == len(flux):
        cols.append(fits.Column(name='PDCSAP_FLUX_ERR', format='D', array=ferr))
    hdu = fits.BinTableHDU.from_columns(cols)
    fits.HDUList([fits.PrimaryHDU(), hdu]).writeto(output_path, overwrite=True)
    return output_path
