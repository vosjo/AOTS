"""ASTRA LC fit → generic AOTS HDF5."""

from __future__ import annotations

import os
import tempfile

import h5py
import numpy as np

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
) -> str:
    if output_path is None:
        fd, output_path = tempfile.mkstemp(suffix='.h5')
        os.close(fd)

    input_data = lc_fit.get('input') or {}
    model_data = lc_fit.get('model') or {}
    in_ph, in_fl, in_fe = _lc_data_to_arrays(input_data, reader)
    mo_ph, mo_fl, mo_fe = _lc_data_to_arrays(model_data, reader)

    with h5py.File(output_path, 'w') as hdf:
        hdf.attrs['type'] = 'LC'
        hdf.attrs['systemname'] = star_name
        hdf.attrs['ra'] = ra
        hdf.attrs['dec'] = dec
        hdf.attrs['name'] = lc_fit.get('label') or f'LC fit — {star_name}'

        if len(in_ph):
            data_grp = hdf.create_group('DATA')
            dtype = np.dtype([('phase', 'f8'), ('flux', 'f8'), ('flux_err', 'f8')])
            err = in_fe if len(in_fe) == len(in_ph) else np.zeros(len(in_ph))
            ds = data_grp.create_dataset('observed', data=np.array(list(zip(in_ph, in_fl, err)), dtype=dtype))
            ds.attrs['datatype'] = 'discrete'
            ds.attrs['xpar'] = 'phase'
            ds.attrs['ypar'] = 'flux'

        if len(mo_ph):
            model_grp = hdf.create_group('MODEL')
            dtype = np.dtype([('phase', 'f8'), ('flux', 'f8')])
            ds = model_grp.create_dataset('model', data=np.array(list(zip(mo_ph, mo_fl)), dtype=dtype))
            ds.attrs['datatype'] = 'continuous'
            ds.attrs['xpar'] = 'phase'
            ds.attrs['ypar'] = 'flux'

        params_grp = hdf.create_group('PARAMETERS')
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
            dtype = np.dtype([('value', 'f8'), ('err_l', 'f8'), ('err_u', 'f8')])
            ds = params_grp.create_dataset(pname, data=np.array([(value, err_l, err_u)], dtype=dtype))
            if unit:
                ds.attrs['unit'] = unit

    return output_path
