"""ASTRA LC fit → AOTS multi-fit HDF5 v2."""

from __future__ import annotations

import os
import tempfile
import uuid

import numpy as np

from analysis.auxil.multi_fit_hdf5 import write_multi_fit_v2
from interop.astra_errors import read_astra_param_errors
from interop.blob_pool import BlobReader


def _lc_data_to_arrays(lc_data: dict, reader: BlobReader) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    phase = np.asarray(reader.get_doubles(lc_data.get('b_phase', -1)), dtype=float)
    flux = np.asarray(reader.get_doubles(lc_data.get('b_flux', -1)), dtype=float)
    ferr = np.asarray(reader.get_doubles(lc_data.get('b_ferr', -1)), dtype=float)
    return phase, flux, ferr


def build_lc_fit_hdf5(
    lc_fit: dict,
    reader: BlobReader,
    *,
    star_name: str,
    ra: float,
    dec: float,
    output_path: str | None = None,
    passband: str = '',
    uploaded_by_user_id: int | None = None,
    uploaded_by_username: str = '',
) -> str:
    if output_path is None:
        fd, output_path = tempfile.mkstemp(suffix='.h5')
        os.close(fd)

    input_data = lc_fit.get('input') or {}
    model_data = lc_fit.get('model') or {}
    in_ph, in_fl, in_fe = _lc_data_to_arrays(input_data, reader)
    mo_ph, mo_fl, mo_fe = _lc_data_to_arrays(model_data, reader)

    measurements_data = None
    data_attrs = {'xlabel': 'phase', 'ylabel': 'flux'}
    if len(in_ph):
        err = in_fe if len(in_fe) == len(in_ph) else np.zeros(len(in_ph))
        dtype = np.dtype([('phase', 'f8'), ('flux', 'f8'), ('flux_err', 'f8')])
        arr = np.array(list(zip(in_ph, in_fl, err)), dtype=dtype)
        measurements_data = {
            'observed': {
                'data': arr,
                'attrs': {
                    'datatype': 'discrete',
                    'xpar': 'phase',
                    'ypar': 'flux',
                },
            },
        }

    model = {}
    if len(mo_ph):
        err = mo_fe if len(mo_fe) == len(mo_ph) else None
        model['model'] = (mo_ph, mo_fl, err)

    parameters: dict[str, tuple] = {}
    lc_param_map = (
        ('p', 'period', 'periodErr', 'd'),
        ('q', 'q', 'qErr', ''),
        ('incl', 'incl', 'inclErr', 'deg'),
        ('r1', 'r1', 'r1Err', ''),
        ('r2', 'r2', 'r2Err', ''),
        ('vscale', 'vscale', 'vscaleErr', 'km/s'),
        ('t1', 't1', 't1Err', ''),
        ('t2', 't2', 't2Err', ''),
        ('t0', 't0BJD', 't0BJDErr', 'd'),
    )
    for pname, vkey, ekey, unit in lc_param_map:
        if vkey not in lc_fit:
            continue
        value = float(lc_fit.get(vkey, 0) or 0)
        _, err_l, err_u = read_astra_param_errors(lc_fit, ekey)
        parameters[pname] = (value, err_l, err_u, unit)

    fit_id = lc_fit.get('id') or str(uuid.uuid4())
    fits = [{
        'id': fit_id,
        'label': lc_fit.get('label') or f'LC fit — {star_name}',
        'is_best_fit': bool(lc_fit.get('isBestFit')),
        'method': lc_fit.get('method') or '',
        'external_id': fit_id,
        'parameters': parameters,
        'model': model,
        'model_xlabel': 'phase',
        'model_ylabel': 'flux',
        'uploaded_by_user_id': uploaded_by_user_id,
        'uploaded_by_username': uploaded_by_username,
    }]
    if passband:
        fits[0]['method'] = passband

    write_multi_fit_v2(
        output_path,
        category='lightcurve_fit',
        hdf5_type='LC',
        measurements_data=measurements_data,
        data_group_attrs=data_attrs if measurements_data else None,
        fits=fits,
        systemname=star_name,
        ra=ra,
        dec=dec,
        name=lc_fit.get('label') or f'LC fit — {star_name}',
    )
    return output_path
