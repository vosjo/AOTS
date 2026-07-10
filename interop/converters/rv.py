"""ASTRA RV container → AOTS RV curve HDF5 v2."""

from __future__ import annotations

import os
import tempfile
import uuid
from typing import Any

import numpy as np

from analysis.auxil.rv_hdf5 import write_rv_curve_v2
from interop.astra_errors import read_astra_param_errors
from interop.parameter_map import map_parameter_name


def _rv_point_time(point: dict) -> float:
    time_obj = point.get('time') or {}
    if isinstance(time_obj, dict) and time_obj.get('bjd') is not None:
        return float(time_obj['bjd'])
    return float(point.get('bjd') or 0.0)


def _fit_parameters(rv_fit: dict) -> dict[str, tuple[float, float, float, str]]:
    mapping = {
        'K': ('KErr', 'km/s'),
        'gamma': ('gammaErr', 'km/s'),
        'period': ('periodErr', 'd'),
        't0': ('t0Err', 'd'),
        'phi': ('phiErr', ''),
        'ecc': ('eccErr', ''),
        'omega': ('omegaErr', 'deg'),
    }
    parameters: dict[str, tuple[float, float, float, str]] = {}
    for astra_key, (err_key, unit) in mapping.items():
        if astra_key not in rv_fit:
            continue
        value = float(rv_fit.get(astra_key, 0) or 0)
        _, err_l, err_u = read_astra_param_errors(rv_fit, err_key)
        mapped = map_parameter_name(astra_key)
        if mapped:
            base, comp = mapped
            pname = base if comp == 0 else f'{base}{comp}'
            parameters[pname] = (value, err_l, err_u, unit)
    return parameters


def build_rv_hdf5(
    rv_container: dict,
    *,
    star_name: str,
    ra: float,
    dec: float,
    output_path: str | None = None,
) -> str:
    if output_path is None:
        fd, output_path = tempfile.mkstemp(suffix='.h5')
        os.close(fd)

    points = rv_container.get('points') or []
    times, rvs, errs = [], [], []
    for pt in points:
        times.append(_rv_point_time(pt))
        rvs.append(float(pt.get('rv', 0) or 0))
        errs.append(float(pt.get('errFormal', pt.get('err', 0)) or 0))

    measurements = None
    if times:
        measurements = {
            'time': np.asarray(times, dtype=float),
            'rv': np.asarray(rvs, dtype=float),
            'err_formal': np.asarray(errs, dtype=float),
        }

    fits_out: list[dict[str, Any]] = []
    for rv_fit in rv_container.get('fits') or []:
        fit_id = rv_fit.get('id') or str(uuid.uuid4())
        fits_out.append({
            'id': fit_id,
            'label': rv_fit.get('method') or rv_fit.get('label') or fit_id,
            'is_best_fit': bool(rv_fit.get('isBestFit')),
            'method': rv_fit.get('method') or '',
            'parameters': _fit_parameters(rv_fit),
        })

    write_rv_curve_v2(
        output_path,
        measurements=measurements,
        fits=fits_out,
        systemname=star_name,
        ra=ra,
        dec=dec,
        name=f'RV curve — {star_name}',
    )
    return output_path
