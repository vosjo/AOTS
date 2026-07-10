"""ASTRA SED model → AOTS SED HDF5 layout."""

from __future__ import annotations

import os
import tempfile

import h5py
import numpy as np

from analysis.auxil.sed_hdf5 import apply_sed_axis_attrs
from interop.astra_errors import read_astra_param_errors
from interop.blob_pool import BlobReader


def _write_ci_scalar(ci_grp, key: str, value: float, err_l: float, err_u: float) -> None:
    value = float(value)
    err_l = float(err_l)
    err_u = float(err_u)
    ci_grp.create_dataset(key, data=value)
    ci_grp.create_dataset(f'{key}_l', data=value - err_l)
    ci_grp.create_dataset(f'{key}_u', data=value + err_u)


def _read_asym(obj: dict) -> tuple[float, float, float]:
    if not isinstance(obj, dict):
        return 0.0, 0.0, 0.0
    value = float(obj.get('v', 0) or 0)
    err_u = float(obj.get('u', 0) or 0)
    err_l = float(obj.get('d', 0) or 0)
    return value, err_l, err_u


def _write_component_ci(ci_grp, component: dict) -> None:
    idx = int(component.get('idx', 1) or 1)

    def ci_key(base: str) -> str:
        return base if idx == 1 else f'{base}{idx}'

    scalar_map = (
        ('teff', 'teff', 'teff_eu', 'teff_ed'),
        ('logg', 'logg', 'logg_eu', 'logg_ed'),
        ('z', 'z', None, None),
        ('vmicro', 'xi', None, None),
        ('he', 'he', 'he_eu', 'he_ed'),
        ('sr', 'sr', 'sr_eu', 'sr_ed'),
    )
    for ci_base, src_val, src_up, src_down in scalar_map:
        value = float(component.get(src_val, 0) or 0)
        if src_up and src_down:
            err_u = float(component.get(src_up, 0) or 0)
            err_l = float(component.get(src_down, 0) or 0)
        else:
            err_l = err_u = 0.0
        if not (value or err_l or err_u):
            continue
        key = ci_key(ci_base)
        _write_ci_scalar(ci_grp, key, value, err_l, err_u)

    for ci_base, json_key, med_json_key in (
        ('rad', 'R', 'R_med'),
        ('m', 'M', 'M_med'),
        ('L', 'L', 'L_med'),
    ):
        value, err_l, err_u = _read_asym(component.get(json_key) or {})
        if value or err_l or err_u:
            _write_ci_scalar(ci_grp, ci_key(ci_base), value, err_l, err_u)
        med_value, med_l, med_u = _read_asym(component.get(med_json_key) or {})
        if med_value or med_l or med_u:
            _write_ci_scalar(ci_grp, f'{ci_key(ci_base)}_med', med_value, med_l, med_u)


def build_sed_hdf5(
    sed_model: dict,
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

    model_wl = np.asarray(reader.get_doubles(sed_model.get('b_modelWl', -1)), dtype=float)
    model_flux = np.asarray(reader.get_doubles(sed_model.get('b_modelFlux', -1)), dtype=float)

    with h5py.File(output_path, 'w') as hdf:
        hdf.attrs['type'] = 'SF'
        info = hdf.create_group('info')
        info.create_dataset('oname', data=star_name)
        info.create_dataset('jradeg', data=float(ra))
        info.create_dataset('jdedeg', data=float(dec))

        results = hdf.create_group('results')
        imin = results.create_group('iminimize')
        ci = imin.create_group('CI')

        global_map = (
            ('ebvSF', 'ebv', 'ebvSFErr'),
            ('ebvSFD', 'ebv_sfd', 'ebvSFDErr'),
            ('chi2r', 'chi2r', None),
            ('logTheta', 'logtheta', 'logThetaErr'),
            ('plx', 'plx', 'plxErr'),
            ('distMode', 'd', 'distModeErr'),
            ('distMed', 'dist_med', 'distMedErr'),
        )
        for src, ci_key, err_key in global_map:
            if src not in sed_model:
                continue
            value = float(sed_model.get(src, 0) or 0)
            if err_key:
                _, err_l, err_u = read_astra_param_errors(sed_model, err_key)
            else:
                err_l = err_u = 0.0
            if value or err_l or err_u:
                _write_ci_scalar(ci, ci_key, value, err_l, err_u)

        for comp in sed_model.get('components') or []:
            if isinstance(comp, dict):
                _write_component_ci(ci, comp)

        # Legacy single-component top-level fields (no components array).
        if not sed_model.get('components'):
            for val_key, ci_base, err_key in (
                ('teff', 'teff', 'teffErr'),
                ('logg', 'logg', 'loggErr'),
            ):
                if val_key not in sed_model:
                    continue
                value = float(sed_model.get(val_key, 0) or 0)
                _, err_l, err_u = read_astra_param_errors(sed_model, err_key)
                if value or err_l or err_u:
                    _write_ci_scalar(ci, f'{ci_base}1', value, err_l, err_u)

            if 'ebvSF' in sed_model and 'ebv' not in ci:
                value = float(sed_model.get('ebvSF', 0) or 0)
                _, err_l, err_u = read_astra_param_errors(sed_model, 'ebvSFErr')
                _write_ci_scalar(ci, 'ebv', value, err_l, err_u)

        if len(model_wl) and len(model_flux):
            master = hdf.create_group('master')
            apply_sed_axis_attrs(master)
            dtype = np.dtype([('wavelength', 'f8'), ('flux', 'f8')])
            n = min(len(model_wl), len(model_flux))
            master.create_dataset(
                'sed',
                data=np.array(list(zip(model_wl[:n], model_flux[:n])), dtype=dtype),
            )

    return output_path
