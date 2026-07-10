"""Map AOTS RV curve HDF5 data to ASTRA .astra RV JSON."""

from __future__ import annotations

from typing import Any

import numpy as np

import uuid

from analysis.auxil.rv_hdf5 import (
    _DATA_META_KEYS,
    get_fit_model_table,
    get_fit_parameters_dict,
    get_measurements_table,
    list_rv_fits,
)
from interop.astra_errors import apply_astra_errors, errors_from_aots_raw
from interop.rv_time import (
    SCALE_BJD,
    astra_time_json_from_epoch,
    bjd_to_mjd,
    guess_time_scale,
)

# AOTS parameter name -> (ASTRA value key, ASTRA error key)
AOTS_RV_TO_ASTRA = {
    'k': ('K', 'KErr'),
    'k1': ('K', 'KErr'),
    'p': ('period', 'periodErr'),
    'v0': ('gamma', 'gammaErr'),
    'v01': ('gamma', 'gammaErr'),
    't0': ('t0', 't0Err'),
    'phi': ('phi', 'phiErr'),
    'e': ('ecc', 'eccErr'),
    'omega': ('omega', 'omegaErr'),
}

# Legacy / ingestion aliases for epoch parameter names in HDF5.
AOTS_RV_PARAM_ALIASES = {
    't00': 't0',
    't': 't0',
}


def _wrap_phase(phi: float) -> float:
    phi = float(phi) % 1.0
    if phi < 0.0:
        phi += 1.0
    return phi


def derive_astra_phi(
    *,
    t_ref: float,
    t0: float,
    period: float,
    eccentric: bool,
) -> float | None:
    """Map AOTS epoch T₀ to ASTRA φ relative to the measurement reference epoch."""
    if not (t_ref > 0.0 and t0 > 0.0 and period > 0.0):
        return None
    sign = -1.0 if eccentric else 1.0
    return _wrap_phase(sign * (t_ref - t0) / period)


def aots_fit_params_to_astra(params: dict[str, Any]) -> dict[str, float | bool]:
    """Convert AOTS PARAMETERS group to ASTRA rvFit JSON keys."""
    out: dict[str, float | bool] = {}
    for pname, raw in params.items():
        value, err_l, err_u = errors_from_aots_raw(raw)
        canonical = AOTS_RV_PARAM_ALIASES.get(pname, pname)
        mapping = AOTS_RV_TO_ASTRA.get(canonical)
        if not mapping:
            continue
        val_key, err_key = mapping
        if value or err_l or err_u:
            out[val_key] = value
            apply_astra_errors(out, err_key=err_key, err_l=err_l, err_u=err_u)
    if out.get('ecc', 0):
        out['eccentric'] = True
    return out


def _rv_measurement_table(data: dict) -> dict[str, np.ndarray] | None:
    mtable = get_measurements_table(data)
    if mtable is not None:
        return mtable
    mtable = get_fit_model_table(data)
    if mtable is not None:
        return mtable
    for fit_meta in list_rv_fits(data):
        mtable = get_fit_model_table(data, fit_meta['id'])
        if mtable is not None:
            return mtable
    return None


def _decode_hdf5_attr(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        return value.decode('utf-8')
    return str(value)


def _time_metadata_from_hdf5_file(path: str) -> tuple[str | None, str | None]:
    import h5py

    try:
        with h5py.File(path, 'r') as hdf:
            if 'DATA' not in hdf:
                return None, None
            data_grp = hdf['DATA']
            xlabel = _decode_hdf5_attr(data_grp.attrs.get('xlabel'))
            if 'measurements' in data_grp:
                ds = data_grp['measurements']
                return _decode_hdf5_attr(ds.attrs.get('xpar')), xlabel
            for name, item in data_grp.items():
                if name in _DATA_META_KEYS or not hasattr(item, 'dtype'):
                    continue
                return _decode_hdf5_attr(item.attrs.get('xpar')), xlabel
    except OSError:
        return None, None
    return None, None


def _measurement_time_context(
    data: dict,
    *,
    hdf5_path: str | None = None,
) -> tuple[str | None, str | None]:
    if hdf5_path:
        return _time_metadata_from_hdf5_file(hdf5_path)
    data_block = data.get('DATA')
    if not isinstance(data_block, dict):
        return None, None
    xlabel = _decode_hdf5_attr(data_block.get('xlabel'))
    measurements = data_block.get('measurements')
    if isinstance(measurements, dict):
        return _decode_hdf5_attr(measurements.get('xpar')), xlabel
    for name, item in data_block.items():
        if name in _DATA_META_KEYS:
            continue
        if isinstance(item, dict) and 'xpar' in item:
            return _decode_hdf5_attr(item.get('xpar')), xlabel
    return None, xlabel


def _table_from_hdf5_dataset(dataset) -> dict[str, np.ndarray] | None:
    from analysis.auxil.plot_analyses import get_attr

    names = getattr(dataset.dtype, 'names', None)
    if not names:
        return None
    xpar = get_attr(dataset, 'xpar', None) or ('time' if 'time' in names else names[0])
    ypar = get_attr(dataset, 'ypar', None) or ('rv' if 'rv' in names else names[min(1, len(names) - 1)])
    columns = {name: np.asarray(dataset[name]) for name in names}
    from analysis.auxil.rv_hdf5 import _table_from_columns
    table = _table_from_columns(columns)
    if table is not None:
        return table
    if xpar in names and ypar in names:
        result = {
            'time': np.asarray(dataset[xpar], dtype=float),
            'rv': np.asarray(dataset[ypar], dtype=float),
        }
        err_key = f'{ypar}_err'
        if err_key in names:
            result['err_formal'] = np.asarray(dataset[err_key], dtype=float)
        elif 'err_formal' in names:
            result['err_formal'] = np.asarray(dataset['err_formal'], dtype=float)
        return result
    return None


def _scan_hdf5_group(group) -> dict[str, np.ndarray] | None:
    if 'measurements' in group:
        table = _table_from_hdf5_dataset(group['measurements'])
        if table is not None:
            return table
    for name, item in group.items():
        if name in _DATA_META_KEYS or name == 'measurements':
            continue
        if not hasattr(item, 'dtype'):
            continue
        table = _table_from_hdf5_dataset(item)
        if table is not None:
            return table
    return None


def rv_points_from_hdf5_file(path: str) -> list[dict]:
    """Read RV points directly from HDF5 when read2dict misses dataset attrs/layout."""
    import h5py

    xpar, xlabel = _time_metadata_from_hdf5_file(path)
    with h5py.File(path, 'r') as hdf:
        if 'DATA' in hdf:
            table = _scan_hdf5_group(hdf['DATA'])
            if table is not None:
                return _points_from_table(table, xpar=xpar, xlabel=xlabel)
        if 'MODEL' in hdf:
            table = _scan_hdf5_group(hdf['MODEL'])
            if table is not None:
                return _points_from_table(table, xpar=xpar, xlabel=xlabel)
        if 'FITS' in hdf:
            fits_grp = hdf['FITS']
            best_id = hdf.attrs.get('best_fit_id')
            if isinstance(best_id, bytes):
                best_id = best_id.decode('utf-8')
            fit_names = [best_id] if best_id in fits_grp else []
            fit_names.extend(name for name in fits_grp.keys() if name not in fit_names)
            for fit_name in fit_names:
                fit_grp = fits_grp[fit_name]
                if 'MODEL' not in fit_grp:
                    continue
                table = _scan_hdf5_group(fit_grp['MODEL'])
                if table is not None:
                    return _points_from_table(table, xpar=xpar, xlabel=xlabel)
    return []


def _points_from_table(
    mtable: dict[str, np.ndarray],
    *,
    xpar: str | None = None,
    xlabel: str | None = None,
    time_scale: str | None = None,
) -> list[dict]:
    times = np.asarray(mtable['time'], dtype=float)
    rvs = np.asarray(mtable['rv'], dtype=float)
    errs = mtable.get('err_formal')
    if errs is None:
        errs = mtable.get('rv_err')
    if errs is None:
        errs = np.zeros(len(times), dtype=float)
    else:
        errs = np.asarray(errs, dtype=float)

    if time_scale is None:
        time_scale = guess_time_scale(times, xpar=xpar, xlabel=xlabel)

    points: list[dict] = []
    for idx in range(len(times)):
        if not np.isfinite(times[idx]) or not np.isfinite(rvs[idx]):
            continue
        points.append({
            'id': str(uuid.uuid4()),
            'rv': float(rvs[idx]),
            'errFormal': float(errs[idx] if idx < len(errs) else 0),
            'time': astra_time_json_from_epoch(
                float(times[idx]),
                scale=time_scale,
                xpar=xpar,
                xlabel=xlabel,
            ),
            'source': 'AOTS',
        })
    return points


def rv_points_from_data(data: dict, *, hdf5_path: str | None = None) -> list[dict]:
    """Build ASTRA RV point dicts from an AOTS RV HDF5 in-memory dict."""
    xpar, xlabel = _measurement_time_context(data, hdf5_path=hdf5_path)
    mtable = _rv_measurement_table(data)
    if mtable is not None:
        return _points_from_table(mtable, xpar=xpar, xlabel=xlabel)
    if hdf5_path:
        return rv_points_from_hdf5_file(hdf5_path)
    return []


def rv_points_from_analysis(analysis) -> list[dict]:
    from analysis.auxil.fileio import read2dict

    path = analysis.datafile.path
    data = read2dict(path)
    return rv_points_from_data(data, hdf5_path=path)


def _reference_epoch_bjd(
    data: dict,
    *,
    hdf5_path: str | None = None,
) -> float | None:
    xpar, xlabel = _measurement_time_context(data, hdf5_path=hdf5_path)
    mtable = _rv_measurement_table(data)
    if mtable is None and hdf5_path:
        import h5py

        try:
            with h5py.File(hdf5_path, 'r') as hdf:
                if 'DATA' in hdf:
                    mtable = _scan_hdf5_group(hdf['DATA'])
        except OSError:
            mtable = None
    if mtable is None:
        return None
    times = np.asarray(mtable['time'], dtype=float)
    finite = times[np.isfinite(times)]
    if finite.size == 0:
        return None
    scale = guess_time_scale(finite, xpar=xpar, xlabel=xlabel)
    earliest = float(np.min(finite))
    if scale == SCALE_BJD:
        return earliest
    return astra_time_json_from_epoch(earliest, scale=scale, xpar=xpar, xlabel=xlabel)['bjd']


def _apply_fit_epoch_metadata(
    fit_entry: dict[str, Any],
    *,
    t_ref_bjd: float | None,
    period: float | None,
    t0: float | None,
    eccentric: bool,
) -> None:
    if t_ref_bjd is not None and t_ref_bjd > 0.0:
        fit_entry['tRefBJD'] = float(t_ref_bjd)
        fit_entry['tRefMJD'] = float(bjd_to_mjd(t_ref_bjd))

    if t_ref_bjd is None or not period or not t0:
        return
    phi = derive_astra_phi(
        t_ref=float(t_ref_bjd),
        t0=float(t0),
        period=float(period),
        eccentric=eccentric,
    )
    if phi is not None:
        fit_entry['phi'] = phi


def rv_fits_from_data(data: dict, *, hdf5_path: str | None = None) -> list[dict]:
    """Build ASTRA RV fit dicts from an AOTS RV HDF5 in-memory dict."""
    t_ref_bjd = _reference_epoch_bjd(data, hdf5_path=hdf5_path)
    fits: list[dict] = []
    for fit_meta in list_rv_fits(data):
        fit_entry: dict[str, Any] = {
            'id': fit_meta['id'],
            'isBestFit': fit_meta['is_best_fit'],
            'method': fit_meta.get('method') or '',
        }
        params = get_fit_parameters_dict(data, fit_meta['id'])
        fit_entry.update(aots_fit_params_to_astra(params))
        eccentric = bool(fit_entry.get('eccentric') or fit_entry.get('ecc', 0))
        _apply_fit_epoch_metadata(
            fit_entry,
            t_ref_bjd=t_ref_bjd,
            period=fit_entry.get('period'),
            t0=fit_entry.get('t0'),
            eccentric=eccentric,
        )
        fits.append(fit_entry)
    return fits
