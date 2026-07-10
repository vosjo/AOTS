"""ASTRA spectral fit → generic AOTS HDF5."""

from __future__ import annotations

import os
import tempfile

import h5py
import numpy as np

from analysis.auxil.sed_hdf5 import apply_sed_axis_attrs
from interop.astra_errors import read_astra_param_errors


def build_spectral_fit_hdf5(
    fit: dict,
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

    model_wl = np.asarray(reader.get_doubles(fit.get('b_modelWl', -1)), dtype=float)
    model_flux = np.asarray(reader.get_doubles(fit.get('b_modelFlux', -1)), dtype=float)
    rebinned = np.asarray(reader.get_doubles(fit.get('b_rebinFlux', -1)), dtype=float)
    rebinned_err = np.asarray(reader.get_doubles(fit.get('b_rebinSig', -1)), dtype=float)

    with h5py.File(output_path, 'w') as hdf:
        hdf.attrs['type'] = 'XF'
        hdf.attrs['systemname'] = star_name
        hdf.attrs['ra'] = ra
        hdf.attrs['dec'] = dec
        hdf.attrs['name'] = f'Spectral fit — {star_name}'

        if len(rebinned):
            data_grp = hdf.create_group('DATA')
            apply_sed_axis_attrs(data_grp, xscale='linear', yscale='linear')
            n = min(len(rebinned), len(model_wl) if len(model_wl) else len(rebinned))
            wl = model_wl[:n] if len(model_wl) >= n else np.arange(n, dtype=float)
            dtype = np.dtype([('wavelength', 'f8'), ('flux', 'f8'), ('flux_err', 'f8')])
            err = rebinned_err[:n] if len(rebinned_err) >= n else np.zeros(n)
            arr = np.array(list(zip(wl, rebinned[:n], err)), dtype=dtype)
            ds = data_grp.create_dataset('observed', data=arr)
            ds.attrs['datatype'] = 'continuous'
            ds.attrs['xpar'] = 'wavelength'
            ds.attrs['ypar'] = 'flux'

        if len(model_wl) and len(model_flux):
            model_grp = hdf.create_group('MODEL')
            apply_sed_axis_attrs(model_grp, xscale='linear', yscale='linear')
            dtype = np.dtype([('wavelength', 'f8'), ('flux', 'f8')])
            arr = np.array(list(zip(model_wl, model_flux)), dtype=dtype)
            ds = model_grp.create_dataset('model', data=arr)
            ds.attrs['datatype'] = 'continuous'
            ds.attrs['xpar'] = 'wavelength'
            ds.attrs['ypar'] = 'flux'

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
        params_grp = hdf.create_group('PARAMETERS')
        for pname, (vkey, ekey, unit) in param_map.items():
            if vkey not in fit:
                continue
            value = float(fit.get(vkey, 0) or 0)
            _, err_l, err_u = read_astra_param_errors(fit, ekey)
            dtype = np.dtype([('value', 'f8'), ('err_l', 'f8'), ('err_u', 'f8')])
            ds = params_grp.create_dataset(pname, data=np.array([(value, err_l, err_u)], dtype=dtype))
            if unit:
                ds.attrs['unit'] = unit

    return output_path
