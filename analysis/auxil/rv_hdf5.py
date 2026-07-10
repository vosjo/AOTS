"""
RV curve HDF5 v2 layout (multi-fit) helpers.

Layout::
    /
      type: "RC"
      rv_curve_format_version: 2
      best_fit_id: "<fit_id>"
      DATA/measurements/   # columns: time, rv, err_formal, err_sys (optional)
      FITS/<fit_id>/       # attrs: isBestFit, method, label, created
        PARAMETERS/        # parameter datasets
        MODEL/             # optional model curve groups
"""

from __future__ import annotations

import uuid
from typing import Any

import h5py
import numpy as np

RV_CURVE_FORMAT_VERSION = 2
LEGACY_FIT_ID = 'legacy'


def is_rv_curve_v2(data: dict) -> bool:
    if data.get('rv_curve_format_version') == RV_CURVE_FORMAT_VERSION:
        return True
    fits = data.get('FITS')
    return isinstance(fits, dict) and bool(fits)


def _fit_attrs(fit_group: dict) -> dict[str, Any]:
    attrs = {}
    for key in ('isBestFit', 'method', 'label', 'created'):
        if key in fit_group:
            attrs[key] = fit_group[key]
    return attrs


def list_rv_fits(data: dict) -> list[dict[str, Any]]:
    """Return fit metadata for API/UI."""
    if not is_rv_curve_v2(data):
        if 'PARAMETERS' in data:
            return [{
                'id': LEGACY_FIT_ID,
                'label': 'Fit',
                'is_best_fit': True,
                'method': '',
            }]
        return []

    fits_block = data.get('FITS', {})
    best_id = data.get('best_fit_id') or ''
    result = []
    for fit_id, fit_group in fits_block.items():
        if not isinstance(fit_group, dict):
            continue
        attrs = _fit_attrs(fit_group)
        is_best = bool(attrs.get('isBestFit')) or fit_id == best_id
        result.append({
            'id': fit_id,
            'label': attrs.get('label') or fit_id,
            'is_best_fit': is_best,
            'method': attrs.get('method') or '',
        })
    if result and not any(f['is_best_fit'] for f in result):
        result[0]['is_best_fit'] = True
    return sorted(result, key=lambda f: (not f['is_best_fit'], f['label']))


def get_best_fit_id(data: dict) -> str | None:
    if not is_rv_curve_v2(data):
        return LEGACY_FIT_ID if 'PARAMETERS' in data else None

    best_id = data.get('best_fit_id')
    if best_id and best_id in data.get('FITS', {}):
        return best_id

    for fit_id, fit_group in data.get('FITS', {}).items():
        if isinstance(fit_group, dict) and fit_group.get('isBestFit'):
            return fit_id
    fits = list_rv_fits(data)
    return fits[0]['id'] if fits else None


def get_fit_parameters_dict(data: dict, fit_id: str | None = None) -> dict:
    """Raw PARAMETERS mapping for a specific fit (or best/legacy)."""
    if is_rv_curve_v2(data):
        fit_id = fit_id or get_best_fit_id(data)
        if not fit_id:
            return {}
        fit_group = data.get('FITS', {}).get(fit_id, {})
        if not isinstance(fit_group, dict):
            return {}
        params = fit_group.get('PARAMETERS', {})
        return params if isinstance(params, dict) else {}

    return data.get('PARAMETERS', {}) if isinstance(data.get('PARAMETERS'), dict) else {}


def has_rv_fits(data: dict) -> bool:
    if is_rv_curve_v2(data):
        return bool(data.get('FITS'))
    return bool(data.get('PARAMETERS'))


_DATA_META_KEYS = frozenset({'xlabel', 'ylabel', 'xscale', 'yscale'})


def _column_arrays(dataset) -> dict[str, np.ndarray] | None:
    if isinstance(dataset, dict):
        return {k: np.asarray(v) for k, v in dataset.items()}
    if hasattr(dataset, 'colnames'):
        return {name: np.asarray(dataset[name]) for name in dataset.colnames}
    if hasattr(dataset, 'dtype') and getattr(dataset.dtype, 'names', None):
        return {name: np.asarray(dataset[name]) for name in dataset.dtype.names}
    return None


def _table_from_columns(columns: dict[str, np.ndarray]) -> dict[str, np.ndarray] | None:
    lower = {name.lower(): name for name in columns}
    time_key = (
        lower.get('time')
        or lower.get('bjd')
        or lower.get('mjd')
        or lower.get('t')
        or lower.get('x')
    )
    rv_key = (
        lower.get('rv')
        or lower.get('vrad')
        or lower.get('y')
        or lower.get('v')
    )
    if not time_key or not rv_key:
        return None
    err_key = (
        lower.get('err_formal')
        or lower.get('rv_err')
        or lower.get(f'{rv_key}_err')
        or lower.get('err')
    )
    result = {
        'time': np.asarray(columns[time_key], dtype=float),
        'rv': np.asarray(columns[rv_key], dtype=float),
    }
    if err_key:
        result['err_formal'] = np.asarray(columns[err_key], dtype=float)
    return result


def _scan_datasets_block(block: dict) -> dict[str, np.ndarray] | None:
    measurements = block.get('measurements')
    if measurements is not None:
        cols = _column_arrays(measurements)
        if cols:
            table = _table_from_columns(cols)
            if table is not None:
                return table

    for name, dataset in block.items():
        if name in _DATA_META_KEYS or name == 'measurements':
            continue
        cols = _column_arrays(dataset)
        if not cols:
            continue
        table = _table_from_columns(cols)
        if table is not None:
            return table
    return None


def get_measurements_table(data: dict) -> dict[str, np.ndarray] | None:
    data_block = data.get('DATA', {})
    if isinstance(data_block, dict):
        table = _scan_datasets_block(data_block)
        if table is not None:
            return table

    model_block = data.get('MODEL', {})
    if isinstance(model_block, dict):
        table = _scan_datasets_block(model_block)
        if table is not None:
            return table
    return None


def get_fit_model_table(data: dict, fit_id: str | None = None) -> dict[str, np.ndarray] | None:
    """Return time/rv columns from a fit's MODEL group (fallback when DATA is empty)."""
    fit_id = fit_id or get_best_fit_id(data)
    if not fit_id:
        return None
    fits_block = data.get('FITS', {})
    if not isinstance(fits_block, dict):
        return None
    fit_group = fits_block.get(fit_id)
    if not isinstance(fit_group, dict):
        return None
    model_block = fit_group.get('MODEL', {})
    if isinstance(model_block, dict):
        return _scan_datasets_block(model_block)
    return None


def _write_parameters_group(parent: h5py.Group, parameters: dict[str, tuple]) -> None:
    """Write PARAMETERS group from {name: (value, err_l, err_u, unit)}."""
    if not parameters:
        return
    grp = parent.create_group('PARAMETERS')
    for name, (value, err_l, err_u, unit) in parameters.items():
        dtype = np.dtype([
            ('value', 'f8'),
            ('err_l', 'f8'),
            ('err_u', 'f8'),
        ])
        arr = np.array([(value, err_l, err_u)], dtype=dtype)
        ds = grp.create_dataset(name, data=arr)
        if unit:
            ds.attrs['unit'] = unit


def _write_model_group(parent: h5py.Group, model: dict[str, np.ndarray], *, xlabel: str = 'time', ylabel: str = 'rv') -> None:
    if not model:
        return
    grp = parent.create_group('MODEL')
    grp.attrs['xlabel'] = xlabel
    grp.attrs['ylabel'] = ylabel
    for name, (x, y, err) in model.items():
        dtype = np.dtype([(xlabel, 'f8'), (ylabel, 'f8'), (f'{ylabel}_err', 'f8')])
        arr = np.array(list(zip(x, y, err)), dtype=dtype)
        ds = grp.create_dataset(name, data=arr)
        ds.attrs['datatype'] = 'continuous'
        ds.attrs['xpar'] = xlabel
        ds.attrs['ypar'] = ylabel


def write_rv_curve_v2(
    path: str,
    *,
    measurements: dict[str, np.ndarray] | None = None,
    fits: list[dict[str, Any]] | None = None,
    systemname: str = '',
    ra: float = 0.0,
    dec: float = 0.0,
    name: str = 'RV curve',
    note: str = '',
    reference: str = '',
) -> None:
    """
    Write an RV curve v2 HDF5 file.

    Each fit dict: id, label, is_best_fit, method, created, parameters, model (optional)
    parameters: {name: (value, err_l, err_u, unit)}
    model: {series_name: (x, y, err)}
    """
    fits = fits or []
    best_id = ''
    for fit in fits:
        if fit.get('is_best_fit'):
            best_id = fit.get('id') or ''
            break
    if not best_id and fits:
        best_id = fits[0].get('id') or str(uuid.uuid4())

    with h5py.File(path, 'w') as hdf:
        hdf.attrs['type'] = 'RC'
        hdf.attrs['rv_curve_format_version'] = RV_CURVE_FORMAT_VERSION
        hdf.attrs['best_fit_id'] = best_id
        hdf.attrs['systemname'] = systemname
        hdf.attrs['ra'] = ra
        hdf.attrs['dec'] = dec
        hdf.attrs['name'] = name
        hdf.attrs['note'] = note
        hdf.attrs['reference'] = reference

        if measurements:
            data_grp = hdf.create_group('DATA')
            data_grp.attrs['xlabel'] = 'time'
            data_grp.attrs['ylabel'] = 'rv'
            cols = []
            names = []
            for col_name, values in measurements.items():
                names.append(col_name)
                cols.append(np.asarray(values, dtype='f8'))
            dtype = np.dtype([(n, 'f8') for n in names])
            arr = np.array([tuple(row) for row in zip(*cols)], dtype=dtype)
            mds = data_grp.create_dataset('measurements', data=arr)
            mds.attrs['datatype'] = 'discrete'
            mds.attrs['xpar'] = 'time'
            mds.attrs['ypar'] = 'rv'

        if fits:
            fits_grp = hdf.create_group('FITS')
            for fit in fits:
                fit_id = fit.get('id') or str(uuid.uuid4())
                fgrp = fits_grp.create_group(fit_id)
                fgrp.attrs['isBestFit'] = bool(fit.get('is_best_fit'))
                fgrp.attrs['label'] = fit.get('label') or fit_id
                fgrp.attrs['method'] = fit.get('method') or ''
                if fit.get('created'):
                    fgrp.attrs['created'] = fit['created']
                _write_parameters_group(fgrp, fit.get('parameters') or {})
                if fit.get('model'):
                    _write_model_group(fgrp, fit['model'])


def migrate_legacy_to_v2(data: dict) -> dict:
    """Convert in-memory legacy layout to v2 structure (for migration command)."""
    if is_rv_curve_v2(data):
        return data

    out = dict(data)
    out['rv_curve_format_version'] = RV_CURVE_FORMAT_VERSION
    out['type'] = out.get('type', 'RC')

    if 'PARAMETERS' in data or 'MODEL' in data:
        fit = {
            'isBestFit': True,
            'label': 'Legacy fit',
            'method': '',
        }
        if 'PARAMETERS' in data:
            fit['PARAMETERS'] = data['PARAMETERS']
        if 'MODEL' in data:
            fit['MODEL'] = data['MODEL']
        out['FITS'] = {LEGACY_FIT_ID: fit}
        out['best_fit_id'] = LEGACY_FIT_ID
        out.pop('PARAMETERS', None)
        out.pop('MODEL', None)

    return out


def write_migrated_v2_file(source_path: str, dest_path: str) -> bool:
    from analysis.auxil.fileio import read2dict

    data = read2dict(source_path)
    migrated = migrate_legacy_to_v2(data)
    if is_rv_curve_v2(migrated) and migrated.get('rv_curve_format_version') == RV_CURVE_FORMAT_VERSION:
        measurements = None
        mtable = get_measurements_table(migrated)
        if mtable:
            measurements = mtable

        fits = []
        for fit_meta in list_rv_fits(migrated):
            fit_id = fit_meta['id']
            params_raw = get_fit_parameters_dict(migrated, fit_id)
            parameters = {}
            for pname, raw in params_raw.items():
                if isinstance(raw, dict):
                    parameters[pname] = (
                        raw.get('value', 0),
                        raw.get('err_l', 0),
                        raw.get('err_u', 0),
                        raw.get('unit', ''),
                    )
                elif hasattr(raw, 'dtype') and raw.dtype.names:
                    row = raw[0]
                    unit = ''
                    parameters[pname] = (float(row['value']), float(row['err_l']), float(row['err_u']), unit)

            fits.append({
                'id': fit_id,
                'label': fit_meta['label'],
                'is_best_fit': fit_meta['is_best_fit'],
                'method': fit_meta['method'],
                'parameters': parameters,
            })

        write_rv_curve_v2(
            dest_path,
            measurements=measurements,
            fits=fits,
            systemname=str(migrated.get('systemname', '')),
            ra=float(migrated.get('ra', 0) or 0),
            dec=float(migrated.get('dec', 0) or 0),
            name=str(migrated.get('name', 'RV curve')),
            note=str(migrated.get('note', '')),
            reference=str(migrated.get('reference', '')),
        )
        return True
    return False
