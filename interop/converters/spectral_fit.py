"""ASTRA spectral fit → AOTS multi-fit HDF5 v2."""

from __future__ import annotations

import os
import tempfile
import uuid

import numpy as np

from analysis.auxil.multi_fit_hdf5 import write_multi_fit_v2
from analysis.auxil.sed_hdf5 import apply_sed_axis_attrs
from interop.astra_errors import read_astra_param_errors
from interop.blob_pool import BlobReader


def build_spectral_fit_hdf5(
    fit: dict,
    reader: BlobReader,
    *,
    star_name: str,
    ra: float,
    dec: float,
    output_path: str | None = None,
    uploaded_by_user_id: int | None = None,
    uploaded_by_username: str = '',
) -> str:
    if output_path is None:
        fd, output_path = tempfile.mkstemp(suffix='.h5')
        os.close(fd)

    model_wl = np.asarray(reader.get_doubles(fit.get('b_modelWl', -1)), dtype=float)
    model_flux = np.asarray(reader.get_doubles(fit.get('b_modelFlux', -1)), dtype=float)
    rebinned = np.asarray(reader.get_doubles(fit.get('b_rebinFlux', -1)), dtype=float)
    rebinned_err = np.asarray(reader.get_doubles(fit.get('b_rebinSig', -1)), dtype=float)

    measurements_data = None
    data_attrs = {'xlabel': 'wavelength', 'ylabel': 'flux', 'xscale': 'linear', 'yscale': 'linear'}
    if len(rebinned):
        n = min(len(rebinned), len(model_wl) if len(model_wl) else len(rebinned))
        wl = model_wl[:n] if len(model_wl) >= n else np.arange(n, dtype=float)
        err = rebinned_err[:n] if len(rebinned_err) >= n else np.zeros(n)
        dtype = np.dtype([('wavelength', 'f8'), ('flux', 'f8'), ('flux_err', 'f8')])
        arr = np.array(list(zip(wl, rebinned[:n], err)), dtype=dtype)
        measurements_data = {
            'observed': {
                'data': arr,
                'attrs': {
                    'datatype': 'continuous',
                    'xpar': 'wavelength',
                    'ypar': 'flux',
                },
            },
        }

    model = {}
    if len(model_wl) and len(model_flux):
        model['model'] = (model_wl, model_flux, None)

    param_map = {
        'teff': ('teff', 'teffErr', 'K'),
        'logg': ('logg', 'loggErr', 'dex'),
        'he': ('he', 'heErr', ''),
        'vsini': ('vsini', 'vsiniErr', 'km/s'),
        'rv': ('rv', 'rvErr', 'km/s'),
        'metal': ('metal', 'metalErr', 'dex'),
        'macro': ('macro', 'macroErr', 'km/s'),
        'micro': ('micro', 'microErr', 'km/s'),
    }
    parameters: dict[str, tuple] = {}
    for pname, (vkey, ekey, unit) in param_map.items():
        if vkey not in fit:
            continue
        value = float(fit.get(vkey, 0) or 0)
        _, err_l, err_u = read_astra_param_errors(fit, ekey)
        parameters[pname] = (value, err_l, err_u, unit)

    fit_id = fit.get('id') or str(uuid.uuid4())
    fits = [{
        'id': fit_id,
        'label': fit.get('label') or fit.get('method') or f'Spectral fit — {star_name}',
        'is_best_fit': bool(fit.get('isBestFit')),
        'method': fit.get('method') or '',
        'external_id': fit_id,
        'parameters': parameters,
        'model': model,
        'model_xlabel': 'wavelength',
        'model_ylabel': 'flux',
        'uploaded_by_user_id': uploaded_by_user_id,
        'uploaded_by_username': uploaded_by_username,
    }]

    write_multi_fit_v2(
        output_path,
        category='spectral_fit',
        hdf5_type='XF',
        measurements_data=measurements_data,
        data_group_attrs=data_attrs if measurements_data else None,
        fits=fits,
        systemname=star_name,
        ra=ra,
        dec=dec,
        name=f'Spectral fit — {star_name}',
    )
    return output_path
