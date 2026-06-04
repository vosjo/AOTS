"""
FITS / file I/O for observations (extracted from model methods).
"""

from collections import OrderedDict

from astropy.io import fits

from observations.auxil import fileio


def _sanitize_fits_header(header):
    result = OrderedDict()
    for key, value in header.items():
        if (
            key != 'comment'
            and key != 'history'
            and key != ''
            and type(value) is not fits.card.Undefined
        ):
            result[key] = value
    return result


def read_fits_header(file_field, hdu=0):
    try:
        header = fits.getheader(file_field.path, hdu)
        return _sanitize_fits_header(header)
    except Exception:
        return OrderedDict()


def read_specfile_spectrum(specfile):
    return fileio.read_spectrum(specfile.specfile.path, return_header=True)


def read_specfile_header(specfile, hdu=0):
    return read_fits_header(specfile.specfile, hdu=hdu)


def read_raw_header(rawspecfile, hdu=0):
    return read_fits_header(rawspecfile.rawfile, hdu=hdu)


def read_lightcurve_data(lightcurve):
    return fileio.read_lightcurve(lightcurve.lcfile.path, return_header=True)


def read_lightcurve_header(lightcurve, hdu=0):
    return read_fits_header(lightcurve.lcfile, hdu=hdu)
