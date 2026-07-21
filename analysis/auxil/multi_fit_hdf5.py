"""
Generic multi-fit HDF5 v2 layout (RV, spectral, LC, SED).

Layout::
    /
      @type
      @<category>_format_version = 2
      @best_fit_id
      DATA/                    # shared measurements
      FITS/<fit_id>/
        @isBestFit, @label, @method, @external_id
        @uploaded_by_user_id, @uploaded_by_username, @created
        PARAMETERS/
        MODEL/
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import h5py
import numpy as np

MULTI_FIT_FORMAT_VERSION = 2
LEGACY_FIT_ID = 'legacy'

CATEGORY_FORMAT_ATTR: dict[str, str] = {
    'rv_curve': 'rv_curve_format_version',
    'spectral_fit': 'spectral_fit_format_version',
    'lightcurve_fit': 'lc_fit_format_version',
    'sed_fit': 'sed_fit_format_version',
}

CATEGORY_HDF5_TYPE: dict[str, str] = {
    'rv_curve': 'RC',
    'spectral_fit': 'XF',
    'lightcurve_fit': 'LC',
    'sed_fit': 'SF',
}

_FIT_ATTR_KEYS = (
    'isBestFit',
    'method',
    'label',
    'created',
    'external_id',
    'uploaded_by_user_id',
    'uploaded_by_username',
)


def format_attr_for_category(category: str | None) -> str | None:
    if not category:
        return None
    return CATEGORY_FORMAT_ATTR.get(category)


def is_multi_fit_v2(data: dict, category: str | None = None) -> bool:
    if category:
        attr = format_attr_for_category(category)
        if attr and data.get(attr) == MULTI_FIT_FORMAT_VERSION:
            return True
    for attr in CATEGORY_FORMAT_ATTR.values():
        if data.get(attr) == MULTI_FIT_FORMAT_VERSION:
            return True
    fits = data.get('FITS')
    return isinstance(fits, dict) and bool(fits)


def _fit_attrs(fit_group: dict) -> dict[str, Any]:
    attrs: dict[str, Any] = {}
    for key in _FIT_ATTR_KEYS:
        if key in fit_group:
            attrs[key] = fit_group[key]
    return attrs


def _decode_attr(value: Any) -> Any:
    if isinstance(value, bytes):
        return value.decode('utf-8', errors='replace')
    return value


def list_fits(data: dict, *, category: str | None = None) -> list[dict[str, Any]]:
    """Return fit metadata for API/UI."""
    if not is_multi_fit_v2(data, category):
        if 'PARAMETERS' in data:
            return [{
                'id': LEGACY_FIT_ID,
                'label': 'Fit',
                'is_best_fit': True,
                'method': '',
                'external_id': '',
                'uploaded_by_user_id': None,
                'uploaded_by_username': '',
                'created': '',
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
        uploaded_by = attrs.get('uploaded_by_user_id')
        if uploaded_by is not None and uploaded_by != '':
            try:
                uploaded_by = int(uploaded_by)
            except (TypeError, ValueError):
                uploaded_by = None
        result.append({
            'id': fit_id,
            'label': _decode_attr(attrs.get('label')) or fit_id,
            'is_best_fit': is_best,
            'method': _decode_attr(attrs.get('method')) or '',
            'external_id': _decode_attr(attrs.get('external_id')) or '',
            'uploaded_by_user_id': uploaded_by,
            'uploaded_by_username': _decode_attr(attrs.get('uploaded_by_username')) or '',
            'created': _decode_attr(attrs.get('created')) or '',
        })
    if result and not any(f['is_best_fit'] for f in result):
        result[0]['is_best_fit'] = True
    return sorted(result, key=lambda f: (not f['is_best_fit'], f['label']))


def get_best_fit_id(data: dict, *, category: str | None = None) -> str | None:
    if not is_multi_fit_v2(data, category):
        return LEGACY_FIT_ID if 'PARAMETERS' in data else None

    best_id = data.get('best_fit_id')
    if best_id and best_id in data.get('FITS', {}):
        return best_id

    for fit_id, fit_group in data.get('FITS', {}).items():
        if isinstance(fit_group, dict) and fit_group.get('isBestFit'):
            return fit_id
    fits = list_fits(data, category=category)
    return fits[0]['id'] if fits else None


def get_fit_parameters_dict(data: dict, fit_id: str | None = None, *, category: str | None = None) -> dict:
    if is_multi_fit_v2(data, category):
        fit_id = fit_id or get_best_fit_id(data, category=category)
        if not fit_id:
            return {}
        fit_group = data.get('FITS', {}).get(fit_id, {})
        if not isinstance(fit_group, dict):
            return {}
        params = fit_group.get('PARAMETERS', {})
        return params if isinstance(params, dict) else {}

    return data.get('PARAMETERS', {}) if isinstance(data.get('PARAMETERS'), dict) else {}


def has_fits(data: dict, *, category: str | None = None) -> bool:
    if is_multi_fit_v2(data, category):
        return bool(data.get('FITS'))
    return bool(data.get('PARAMETERS'))


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


def _write_model_group(
    parent: h5py.Group,
    model: dict[str, Any],
    *,
    xlabel: str = 'x',
    ylabel: str = 'y',
) -> None:
    if not model:
        return
    grp = parent.create_group('MODEL')
    grp.attrs['xlabel'] = xlabel
    grp.attrs['ylabel'] = ylabel
    for name, series in model.items():
        datatype = 'continuous'
        label = None
        if isinstance(series, dict):
            x, y, err = series['data'] if 'data' in series else (series['x'], series['y'], series.get('err'))
            datatype = series.get('datatype') or datatype
            label = series.get('label')
        else:
            x, y, err = series
        err_arr = err if err is not None else np.zeros_like(np.asarray(x, dtype=float))
        dtype = np.dtype([(xlabel, 'f8'), (ylabel, 'f8'), (f'{ylabel}_err', 'f8')])
        arr = np.array(list(zip(x, y, err_arr)), dtype=dtype)
        ds = grp.create_dataset(name, data=arr)
        ds.attrs['datatype'] = datatype
        ds.attrs['xpar'] = xlabel
        ds.attrs['ypar'] = ylabel
        if label:
            ds.attrs['label'] = label


def repair_model_datatypes(path: str) -> int:
    """
    Fix MODEL series wrongly marked continuous after multi-fit migration.

    Synthetic photometry (e.g. Iflux) must stay ``discrete`` so plots show
    markers instead of a line through the observed bandpasses.
    Returns number of datasets updated.
    """
    updated = 0
    with h5py.File(path, 'r+') as hdf:
        obs_len = None
        if 'DATA' in hdf:
            for name in hdf['DATA']:
                item = hdf['DATA'][name]
                if isinstance(item, h5py.Dataset) and len(item.shape) == 1:
                    obs_len = item.shape[0]
                    break

        model_groups: list[h5py.Group] = []
        if 'MODEL' in hdf:
            model_groups.append(hdf['MODEL'])
        if 'FITS' in hdf:
            for fid in hdf['FITS']:
                if 'MODEL' in hdf['FITS'][fid]:
                    model_groups.append(hdf['FITS'][fid]['MODEL'])

        for grp in model_groups:
            lengths = {
                name: grp[name].shape[0]
                for name in grp
                if isinstance(grp[name], h5py.Dataset) and len(grp[name].shape) == 1
            }
            if not lengths:
                continue
            max_len = max(lengths.values())
            for name, length in lengths.items():
                ds = grp[name]
                current = ds.attrs.get('datatype')
                if isinstance(current, bytes):
                    current = current.decode('utf-8', errors='replace')
                should_be_discrete = (
                    name.lower() in {'iflux', 'synth', 'phot', 'obs'}
                    or (obs_len is not None and length == obs_len and length < max_len)
                    or (length < max_len and max_len >= 100 and length <= 500)
                )
                if should_be_discrete and current != 'discrete':
                    ds.attrs['datatype'] = 'discrete'
                    if 'label' not in ds.attrs and name.lower() == 'iflux':
                        ds.attrs['label'] = 'Synth. photometry'
                    updated += 1
    return updated


def _apply_fit_group_attrs(
    grp: h5py.Group,
    fit: dict[str, Any],
    *,
    uploaded_by_user_id: int | None = None,
    uploaded_by_username: str = '',
) -> None:
    grp.attrs['isBestFit'] = bool(fit.get('is_best_fit'))
    grp.attrs['label'] = fit.get('label') or grp.name.split('/')[-1]
    grp.attrs['method'] = fit.get('method') or ''
    if fit.get('external_id'):
        grp.attrs['external_id'] = fit['external_id']
    created = fit.get('created') or datetime.now(timezone.utc).isoformat()
    grp.attrs['created'] = created
    uid = fit.get('uploaded_by_user_id', uploaded_by_user_id)
    if uid is not None:
        grp.attrs['uploaded_by_user_id'] = int(uid)
    uname = fit.get('uploaded_by_username') or uploaded_by_username
    if uname:
        grp.attrs['uploaded_by_username'] = uname


def _numpy_for_hdf5(data: Any) -> np.ndarray:
    """Return an HDF5-writable ndarray (unicode/object fields → bytes)."""
    arr = np.asanyarray(data)
    if arr.dtype.kind in ('U', 'O'):
        return arr.astype('S')
    if not arr.dtype.names:
        return arr

    fields: list[tuple[str, Any]] = []
    columns: dict[str, np.ndarray] = {}
    for name in arr.dtype.names:
        field_dtype = arr.dtype.fields[name][0]  # type: ignore[index]
        col = arr[name]
        if field_dtype.kind in ('U', 'O'):
            byte_len = max(int(field_dtype.itemsize) * 4, 8) if field_dtype.kind == 'U' else 64
            byte_dt = f'S{byte_len}'
            if col.dtype.kind == 'U':
                encoded = np.char.encode(col.astype('U'), 'utf-8')
            else:
                encoded = np.asarray(col, dtype=byte_dt)
            columns[name] = encoded
            fields.append((name, byte_dt))
        else:
            columns[name] = col
            fields.append((name, field_dtype))
    dtype = np.dtype(fields)
    out = np.empty(arr.shape, dtype=dtype)
    for name in arr.dtype.names:
        out[name] = columns[name]
    return out


def _copy_h5_group(src: h5py.Group, dest_parent: h5py.Group, name: str) -> h5py.Group:
    """Shallow-copy a group and its datasets into dest_parent."""
    dest = dest_parent.create_group(name)
    for key, val in src.attrs.items():
        dest.attrs[key] = val
    for key in src.keys():
        item = src[key]
        if isinstance(item, h5py.Group):
            _copy_h5_group(item, dest, key)
        else:
            dest.copy(item, key)
    return dest


def write_multi_fit_v2(
    path: str,
    *,
    category: str,
    hdf5_type: str | None = None,
    measurements_data: dict[str, Any] | None = None,
    data_group_attrs: dict[str, Any] | None = None,
    fits: list[dict[str, Any]] | None = None,
    systemname: str = '',
    ra: float = 0.0,
    dec: float = 0.0,
    name: str = '',
    note: str = '',
    reference: str = '',
    root_attrs: dict[str, Any] | None = None,
) -> None:
    fits = fits or []
    fmt_attr = format_attr_for_category(category) or 'fit_format_version'
    hdf5_type = hdf5_type or CATEGORY_HDF5_TYPE.get(category, '??')

    best_id = ''
    for fit in fits:
        if fit.get('is_best_fit'):
            best_id = fit.get('id') or ''
            break
    if not best_id and fits:
        best_id = fits[0].get('id') or str(uuid.uuid4())

    with h5py.File(path, 'w') as hdf:
        hdf.attrs['type'] = hdf5_type
        hdf.attrs[fmt_attr] = MULTI_FIT_FORMAT_VERSION
        hdf.attrs['best_fit_id'] = best_id
        hdf.attrs['systemname'] = systemname
        hdf.attrs['ra'] = ra
        hdf.attrs['dec'] = dec
        hdf.attrs['name'] = name
        hdf.attrs['note'] = note
        hdf.attrs['reference'] = reference
        if root_attrs:
            for key, val in root_attrs.items():
                hdf.attrs[key] = val

        if measurements_data:
            data_grp = hdf.create_group('DATA')
            if data_group_attrs:
                for key, val in data_group_attrs.items():
                    data_grp.attrs[key] = val
            for ds_name, payload in measurements_data.items():
                if isinstance(payload, np.ndarray):
                    data_grp.create_dataset(ds_name, data=_numpy_for_hdf5(payload))
                elif isinstance(payload, dict) and 'data' in payload:
                    ds = data_grp.create_dataset(ds_name, data=_numpy_for_hdf5(payload['data']))
                    for ak, av in (payload.get('attrs') or {}).items():
                        ds.attrs[ak] = av

        if fits:
            fits_grp = hdf.create_group('FITS')
            for fit in fits:
                fit_id = fit.get('id') or str(uuid.uuid4())
                fgrp = fits_grp.create_group(fit_id)
                _apply_fit_group_attrs(fgrp, fit)
                if fit.get('parameters'):
                    _write_parameters_group(fgrp, fit['parameters'])
                if fit.get('model'):
                    _write_model_group(
                        fgrp,
                        fit['model'],
                        xlabel=fit.get('model_xlabel', 'x'),
                        ylabel=fit.get('model_ylabel', 'y'),
                    )


def set_best_fit(path: str, fit_id: str) -> bool:
    """Mark fit_id as best in an on-disk HDF5 file. Returns False if fit missing."""
    with h5py.File(path, 'r+') as hdf:
        if 'FITS' not in hdf or fit_id not in hdf['FITS']:
            return False
        hdf.attrs['best_fit_id'] = fit_id
        for fid in hdf['FITS'].keys():
            hdf['FITS'][fid].attrs['isBestFit'] = (fid == fit_id)
    return True


def append_fit(
    path: str,
    fit: dict[str, Any],
    *,
    uploaded_by_user_id: int | None = None,
    uploaded_by_username: str = '',
    set_as_best: bool = False,
) -> str:
    """Append a fit to an existing multi-fit HDF5 file. Returns fit_id."""
    fit_id = fit.get('id') or str(uuid.uuid4())
    with h5py.File(path, 'a') as hdf:
        if 'FITS' not in hdf:
            hdf.create_group('FITS')
        if fit_id in hdf['FITS']:
            raise ValueError(f'Fit id already exists: {fit_id}')
        fgrp = hdf['FITS'].create_group(fit_id)
        fit_with_id = dict(fit, id=fit_id)
        if set_as_best or not list(hdf['FITS'].keys()) or fit.get('is_best_fit'):
            fit_with_id['is_best_fit'] = True
        _apply_fit_group_attrs(
            fgrp,
            fit_with_id,
            uploaded_by_user_id=uploaded_by_user_id,
            uploaded_by_username=uploaded_by_username,
        )
        if fit.get('parameters'):
            _write_parameters_group(fgrp, fit['parameters'])
        if fit.get('model'):
            _write_model_group(
                fgrp,
                fit['model'],
                xlabel=fit.get('model_xlabel', 'x'),
                ylabel=fit.get('model_ylabel', 'y'),
            )
        if fit.get('hdf5_fit_path'):
            with h5py.File(fit['hdf5_fit_path'], 'r') as src:
                if 'PARAMETERS' in src:
                    _copy_h5_group(src['PARAMETERS'], fgrp, 'PARAMETERS')
                elif 'FITS' in src:
                    first_fit = next(iter(src['FITS'].values()))
                    if 'PARAMETERS' in first_fit:
                        _copy_h5_group(first_fit['PARAMETERS'], fgrp, 'PARAMETERS')
                if 'MODEL' in src:
                    _copy_h5_group(src['MODEL'], fgrp, 'MODEL')
                elif 'FITS' in src:
                    first_fit = next(iter(src['FITS'].values()))
                    if 'MODEL' in first_fit:
                        _copy_h5_group(first_fit['MODEL'], fgrp, 'MODEL')

        is_best = bool(fgrp.attrs.get('isBestFit'))
        if is_best:
            hdf.attrs['best_fit_id'] = fit_id
            for fid in hdf['FITS'].keys():
                hdf['FITS'][fid].attrs['isBestFit'] = (fid == fit_id)
        elif 'best_fit_id' not in hdf.attrs or not hdf.attrs['best_fit_id']:
            hdf.attrs['best_fit_id'] = fit_id
            fgrp.attrs['isBestFit'] = True
    return fit_id


def remove_fit(path: str, fit_id: str) -> bool:
    """Remove a fit group. Reassigns best_fit_id if needed."""
    with h5py.File(path, 'r+') as hdf:
        if 'FITS' not in hdf or fit_id not in hdf['FITS']:
            return False
        was_best = hdf.attrs.get('best_fit_id') == fit_id
        del hdf['FITS'][fit_id]
        remaining = list(hdf['FITS'].keys())
        if not remaining:
            hdf.attrs['best_fit_id'] = ''
            return True
        if was_best:
            new_best = remaining[0]
            hdf.attrs['best_fit_id'] = new_best
            for fid in remaining:
                hdf['FITS'][fid].attrs['isBestFit'] = (fid == new_best)
    return True


def update_fit_metadata(path: str, fit_id: str, *, label: str | None = None, method: str | None = None) -> bool:
    with h5py.File(path, 'r+') as hdf:
        if 'FITS' not in hdf or fit_id not in hdf['FITS']:
            return False
        grp = hdf['FITS'][fit_id]
        if label is not None:
            grp.attrs['label'] = label
        if method is not None:
            grp.attrs['method'] = method
    return True
