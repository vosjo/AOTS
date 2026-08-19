"""
RV curve HDF5 v2 layout (multi-fit) helpers.

Delegates generic multi-fit I/O to analysis.auxil.multi_fit_hdf5.
"""

from __future__ import annotations

import uuid
from typing import Any

import h5py
import numpy as np

from analysis.auxil.multi_fit_hdf5 import (
    LEGACY_FIT_ID,
    MULTI_FIT_FORMAT_VERSION,
    append_fit,
    has_fits,
    is_multi_fit_v2,
    list_fits,
    remove_fit,
    set_best_fit,
    update_fit_metadata,
    write_multi_fit_v2,
)
from analysis.auxil.multi_fit_hdf5 import (
    get_best_fit_id as _get_best_fit_id,
)
from analysis.auxil.multi_fit_hdf5 import (
    get_fit_parameters_dict as _get_fit_parameters_dict,
)

RV_CURVE_FORMAT_VERSION = MULTI_FIT_FORMAT_VERSION


def is_rv_curve_v2(data: dict) -> bool:
    return is_multi_fit_v2(data, 'rv_curve')


def list_rv_fits(data: dict) -> list[dict[str, Any]]:
    return list_fits(data, category='rv_curve')


def get_best_fit_id(data: dict) -> str | None:
    return _get_best_fit_id(data, category='rv_curve')


def get_fit_parameters_dict(data: dict, fit_id: str | None = None) -> dict:
    return _get_fit_parameters_dict(data, fit_id, category='rv_curve')


def has_rv_fits(data: dict) -> bool:
    return has_fits(data, category='rv_curve')


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
        arr = np.array(list(zip(x, y, err, strict=False)), dtype=dtype)
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
    measurements_data = None
    data_attrs = {'xlabel': 'time', 'ylabel': 'rv'}
    if measurements:
        cols = []
        names = []
        for col_name, values in measurements.items():
            names.append(col_name)
            cols.append(np.asarray(values, dtype='f8'))
        dtype = np.dtype([(n, 'f8') for n in names])
        arr = np.array([tuple(row) for row in zip(*cols, strict=False)], dtype=dtype)
        measurements_data = {
            'measurements': {
                'data': arr,
                'attrs': {
                    'datatype': 'discrete',
                    'xpar': 'time',
                    'ypar': 'rv',
                },
            },
        }

    write_multi_fit_v2(
        path,
        category='rv_curve',
        hdf5_type='RC',
        measurements_data=measurements_data,
        data_group_attrs=data_attrs if measurements else None,
        fits=fits,
        systemname=systemname,
        ra=ra,
        dec=dec,
        name=name,
        note=note,
        reference=reference,
    )


def migrate_legacy_to_v2(data: dict) -> dict:
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
                    parameters[pname] = (float(row['value']), float(row['err_l']), float(row['err_u']), '')

            fits.append({
                'id': fit_id,
                'label': fit_meta['label'],
                'is_best_fit': fit_meta['is_best_fit'],
                'method': fit_meta['method'],
                'parameters': parameters,
                'uploaded_by_user_id': fit_meta.get('uploaded_by_user_id'),
                'uploaded_by_username': fit_meta.get('uploaded_by_username', ''),
                'external_id': fit_meta.get('external_id', ''),
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


__all__ = [
    'RV_CURVE_FORMAT_VERSION',
    'LEGACY_FIT_ID',
    'append_fit',
    'get_best_fit_id',
    'get_fit_model_table',
    'get_fit_parameters_dict',
    'get_measurements_table',
    'has_rv_fits',
    'is_rv_curve_v2',
    'list_rv_fits',
    'migrate_legacy_to_v2',
    'remove_fit',
    'set_best_fit',
    'update_fit_metadata',
    'write_migrated_v2_file',
    'write_rv_curve_v2',
]
