"""Map AOTS SED-fit HDF5 data to ASTRA .astra sedModel JSON."""

from __future__ import annotations

from typing import Any

import h5py
import numpy as np

from analysis.auxil.fileio import read2dict
from analysis.auxil.read_analyses import (
    basic_info_generic,
    basic_info_special_sedfit,
    get_parameters,
    get_parameters_generic,
)
from analysis.categories import is_isis_sed_hdf5_layout
from interop.astra_errors import apply_astra_errors
from analysis.models import Analysis
from interop.blob_pool import BlobPool

# Homogenised AOTS parameter key (teff1, rad2, …) → ASTRA scalar fields.
_COMPONENT_SCALARS: tuple[tuple[str, str, str | None, str | None], ...] = (
    ('teff', 'teff', 'teff_eu', 'teff_ed'),
    ('logg', 'logg', 'logg_eu', 'logg_ed'),
    ('z', 'z', None, None),
    ('vmicro', 'xi', None, None),
    ('he', 'he', 'he_eu', 'he_ed'),
    ('sr', 'sr', 'sr_eu', 'sr_ed'),
)

# CI keys at system level → ASTRA sedModel top-level fields.
_GLOBAL_CI_KEYS: tuple[tuple[str, str, str | None], ...] = (
    ('ebv', 'ebvSF', 'ebvSFErr'),
    ('ebv_sfd', 'ebvSFD', 'ebvSFDErr'),
    ('chi2', 'chi2r', None),
    ('chi2r', 'chi2r', None),
    ('logtheta', 'logTheta', 'logThetaErr'),
    ('logTheta', 'logTheta', 'logThetaErr'),
    ('plx', 'plx', 'plxErr'),
    ('d', 'distMode', 'distModeErr'),
    ('dist', 'distMode', 'distModeErr'),
    ('dist_med', 'distMed', 'distMedErr'),
)

# Per-component asymmetric quantities in CI (prefix + component index).
_ASYMMETRIC_BASES: tuple[tuple[str, str, str], ...] = (
    ('rad', 'R', 'R_med'),
    ('R', 'R', 'R_med'),
    ('m', 'M', 'M_med'),
    ('M', 'M', 'M_med'),
    ('L', 'L', 'L_med'),
)


def _scalar_from_ci_value(raw: Any) -> float:
    if raw is None:
        return 0.0
    if isinstance(raw, (int, float, np.floating, np.integer)):
        return float(raw)
    if isinstance(raw, (bytes, str)):
        return float(str(raw).strip() or 0)
    if hasattr(raw, 'colnames'):
        if len(raw) == 0:
            return 0.0
        row = raw[0]
        col = raw.colnames[0]
        return float(row[col])
    if isinstance(raw, np.ndarray):
        if raw.ndim == 0:
            return float(raw)
        if raw.dtype.names:
            return float(raw[raw.dtype.names[0]].reshape(-1)[0])
        if raw.size:
            return float(raw.flat[0])
    if hasattr(raw, 'dtype') and getattr(raw.dtype, 'names', None):
        row = raw[0]
        names = raw.dtype.names
        return float(row[names[0]])
    if hasattr(raw, '__len__') and len(raw):
        return float(raw[0])
    try:
        return float(raw)
    except (TypeError, ValueError):
        return 0.0


def _h5_dataset_scalar(dataset) -> float | str:
    value = dataset[()]
    if isinstance(value, bytes):
        return value.decode('utf-8')
    if isinstance(value, str):
        return value
    if isinstance(value, np.ndarray):
        if value.dtype.kind in ('S', 'U'):
            item = value.reshape(-1)[0]
            return item.decode('utf-8') if isinstance(item, bytes) else str(item)
        return float(value.reshape(-1)[0])
    return float(value)


def _read_flat_ci(path: str) -> dict[str, float | str]:
    """Read CI datasets as plain scalars (ISIS / interop layout)."""
    flat: dict[str, float | str] = {}
    try:
        with h5py.File(path, 'r') as hdf:
            ci = None
            for method in ('iminimize', 'igrid_search'):
                key = f'results/{method}/CI'
                if key in hdf:
                    ci = hdf[key]
                    break
            if ci is None:
                return flat
            for name in ci.keys():
                item = ci[name]
                if isinstance(item, h5py.Dataset):
                    val = _h5_dataset_scalar(item)
                    if isinstance(val, str):
                        flat[name] = val
                    else:
                        flat[name] = float(val)
    except OSError:
        return {}
    return flat


def _read_sed_info(path: str) -> tuple[str, float, float]:
    try:
        with h5py.File(path, 'r') as hdf:
            if 'info' not in hdf:
                return '', 0.0, 0.0
            info = hdf['info']
            name = ''
            if 'oname' in info:
                raw = _h5_dataset_scalar(info['oname'])
                name = raw if isinstance(raw, str) else str(raw)
            ra = float(_h5_dataset_scalar(info['jradeg'])) if 'jradeg' in info else 0.0
            dec = float(_h5_dataset_scalar(info['jdedeg'])) if 'jdedeg' in info else 0.0
            return name, ra, dec
    except OSError:
        return '', 0.0, 0.0


def _homogenised_params_from_flat_ci(ci: dict[str, float | str]) -> dict[str, list]:
    """Mirror ``get_parameters_special_sedfit`` for scalar CI dicts."""
    upper, lower = '_u', '_l'

    def _ci_tuple(key: str, unit: str) -> list | None:
        if key not in ci or f'{key}{upper}' not in ci or f'{key}{lower}' not in ci:
            return None
        value = float(ci[key])
        return [
            value,
            float(ci[f'{key}{upper}']) - value,
            value - float(ci[f'{key}{lower}']),
            unit,
        ]

    def _add_component_pair(base: str, unit: str, results: dict) -> None:
        t1 = _ci_tuple(base, unit)
        if t1 is not None:
            results[f'{base}1'] = t1
        t2 = _ci_tuple(f'{base}2', unit)
        if t2 is not None:
            results[f'{base}2'] = t2

    results: dict[str, list] = {}
    t = _ci_tuple('ebv', 'mag')
    if t is not None:
        results['ebv'] = t
    for base, unit in (
        ('teff', 'K'),
        ('logg', 'dex'),
        ('z', 'dex'),
        ('vmicro', 'km/s'),
        ('vrot', 'km/s'),
        ('dilution', ''),
        ('rad', 'solRad'),
        ('L', 'solLum'),
        ('m', 'solMass'),
        ('he', ''),
        ('sr', ''),
    ):
        _add_component_pair(base, unit, results)
        if base in ('rad', 'L', 'm'):
            if base == 'rad':
                med_keys = ('rad_med', 'rad2_med')
            elif base == 'L':
                med_keys = ('L_med', 'L2_med')
            else:
                med_keys = ('m_med', 'm2_med')
            t_med = _ci_tuple(med_keys[0], unit)
            if t_med is not None:
                results[f'{base}1_med'] = t_med
            t_med2 = _ci_tuple(med_keys[1], unit)
            if t_med2 is not None:
                results[f'{base}2_med'] = t_med2
    return results


def _ci_bounds(ci: dict, key: str) -> tuple[float, float, float]:
    """Return (value, err_up, err_down) from AOTS CI (_l/_u are interval bounds)."""
    if key not in ci:
        return 0.0, 0.0, 0.0
    value = _scalar_from_ci_value(ci[key])
    err_up = err_down = 0.0
    upper_key, lower_key = f'{key}_u', f'{key}_l'
    if upper_key in ci:
        err_up = max(0.0, _scalar_from_ci_value(ci[upper_key]) - value)
    if lower_key in ci:
        err_down = max(0.0, value - _scalar_from_ci_value(ci[lower_key]))
    return value, err_up, err_down


def _get_ci_group(data: dict) -> dict | None:
    results = data.get('results')
    if not isinstance(results, dict):
        return None
    for method in ('iminimize', 'igrid_search'):
        method_grp = results.get(method)
        if isinstance(method_grp, dict):
            ci = method_grp.get('CI')
            if isinstance(ci, dict):
                return ci
    return None


def _param_tuple(params: dict, key: str) -> tuple[float, float, float]:
    entry = params.get(key)
    if not entry or len(entry) < 3:
        return 0.0, 0.0, 0.0
    return float(entry[0]), float(entry[1]), float(entry[2])


def _lookup_param(params: dict, base: str, component: int) -> tuple[float, float, float]:
    """Resolve homogenised keys (teff1) and legacy single-component keys (teff)."""
    keys = [_homogenised_key(base, component)]
    if component == 1:
        keys.append(base)
    for key in keys:
        value, err_l, err_u = _param_tuple(params, key)
        if value or err_l or err_u:
            return value, err_l, err_u
    return 0.0, 0.0, 0.0


def _decode_text(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode('utf-8')
    if isinstance(value, np.ndarray) and value.dtype.kind in ('S', 'U'):
        item = value.reshape(-1)[0]
        return item.decode('utf-8') if isinstance(item, bytes) else str(item)
    return str(value or '')


def _observed_from_data(data: dict) -> list[dict]:
    """Map AOTS generic SED-fit DATA/Obs table to ASTRA observed points."""
    data_grp = data.get('DATA')
    if not isinstance(data_grp, dict):
        return []
    obs = data_grp.get('Obs')
    if obs is None or not hasattr(obs, 'dtype'):
        return []

    names = obs.dtype.names or ()
    points: list[dict] = []
    for row in obs:
        wl = float(row['wave']) if 'wave' in names else 0.0
        flux = float(row['flux']) if 'flux' in names else 0.0
        flux_err = float(row['flux_err']) if 'flux_err' in names else 0.0
        band = _decode_text(row['photband']) if 'photband' in names else ''
        if wl <= 0 or flux <= 0:
            continue
        point = {
            'passband': band,
            'system': 'AOTS',
            'l': wl,
            'f': flux,
            'type': 'flux',
            'flag': 0,
        }
        if flux_err > 0:
            point['fmin'] = max(0.0, flux - flux_err)
            point['fmax'] = flux + flux_err
        points.append(point)
    return points


def _extract_model_tmap(data: dict, bp: BlobPool) -> tuple[int | None, int | None]:
    model_grp = data.get('MODEL')
    if not isinstance(model_grp, dict):
        return None, None
    tmap = model_grp.get('tmap')
    if tmap is None or not hasattr(tmap, 'dtype'):
        return None, None
    names = tmap.dtype.names or ()
    wl_key = 'wave' if 'wave' in names else names[0] if names else None
    fl_key = 'flux' if 'flux' in names else names[1] if len(names) > 1 else None
    if not wl_key or not fl_key:
        return None, None
    wl = np.asarray(tmap[wl_key], dtype=float).flatten()
    fl = np.asarray(tmap[fl_key], dtype=float).flatten()
    if len(wl) == 0 or len(fl) == 0:
        return None, None
    n = min(len(wl), len(fl))
    return bp.add_doubles(list(map(float, wl[:n]))), bp.add_doubles(list(map(float, fl[:n])))


def _homogenised_key(base: str, component: int) -> str:
    if component in (1, 2):
        return f'{base}{component}'
    return base


def _ci_key(base: str, component: int) -> str:
    if component == 1:
        return base
    return f'{base}{component}'


def _astra_asym_json(value: float, err_up: float, err_down: float) -> dict:
    return {'v': float(value), 'u': float(err_up), 'd': float(err_down)}


def _count_components(params: dict, ci: dict | None) -> int:
    for base in ('teff', 'logg', 'z', 'vmicro', 'rad', 'R', 'L'):
        if _param_tuple(params, _homogenised_key(base, 2))[0]:
            return 2
        if ci and _ci_key(base, 2) in ci:
            return 2
    return 1


def _fill_scalar_component_fields(
    comp: dict,
    *,
    component: int,
    params: dict,
    ci: dict | None,
) -> None:
    for aots_base, astra_val, eu_key, ed_key in _COMPONENT_SCALARS:
        value, err_l, err_u = _lookup_param(params, aots_base, component)
        if not value and ci is not None:
            ci_value, err_up, err_down = _ci_bounds(ci, _ci_key(aots_base, component))
            value, err_l, err_u = ci_value, err_down, err_up
        if not (value or err_l or err_u):
            continue
        comp[astra_val] = value
        if eu_key and ed_key:
            comp[eu_key] = err_u
            comp[ed_key] = err_l
        elif astra_val == 'xi':
            comp['xi_st'] = 0
        elif astra_val == 'z':
            comp['z_st'] = 0


def _ci_candidate_keys(base: str, component: int) -> list[str]:
    """Possible CI dataset names for a component quantity."""
    keys: list[str] = []
    if component == 1:
        keys.extend([base, f'{base}1'])
    else:
        keys.append(f'{base}{component}')
    upper = base.upper()
    if upper != base:
        keys.append(upper if component == 1 else f'{upper}{component}')
    return keys


def _asym_from_sources(
    *,
    component: int,
    base: str,
    params: dict,
    ci: dict | None,
) -> tuple[dict, dict]:
    """Return (mode, median) AsymmetricValue JSON for one R/M/L-like quantity."""
    mode_key = _homogenised_key(base, component)
    value, err_l, err_u = _lookup_param(params, base, component)
    med_value, med_l, med_u = _param_tuple(params, f'{mode_key}_med')
    if component == 1 and not med_value:
        med_value, med_l, med_u = _param_tuple(params, f'{base}_med')

    if not value and ci is not None:
        for ci_key in _ci_candidate_keys(base, component):
            if ci_key in ci:
                value, err_up, err_down = _ci_bounds(ci, ci_key)
                err_l, err_u = err_down, err_up
                break

    if not med_value and ci is not None:
        med_candidates = []
        for ci_key in _ci_candidate_keys(base, component):
            med_candidates.append(f'{ci_key}_med')
        if component == 1:
            med_candidates.append(f'{base}_med')
        for med_ci_key in med_candidates:
            if med_ci_key in ci:
                med_value, med_up, med_down = _ci_bounds(ci, med_ci_key)
                med_l, med_u = med_down, med_up
                break

    mode = _astra_asym_json(value, err_u, err_l)
    median = _astra_asym_json(med_value, med_u, med_l)
    return mode, median


def _fill_asymmetric_component_fields(
    comp: dict,
    *,
    component: int,
    params: dict,
    ci: dict | None,
) -> None:
    seen: set[str] = set()
    for base, astra_mode, astra_median in _ASYMMETRIC_BASES:
        if astra_mode in seen:
            continue
        mode, median = _asym_from_sources(
            component=component,
            base=base,
            params=params,
            ci=ci,
        )
        if mode['v'] or mode['u'] or mode['d']:
            comp[astra_mode] = mode
            seen.add(astra_mode)
        if median['v'] or median['u'] or median['d']:
            comp[astra_median] = median


def _build_component(
    component: int,
    *,
    params: dict,
    ci: dict | None,
) -> dict:
    comp: dict = {'idx': component}
    _fill_scalar_component_fields(comp, component=component, params=params, ci=ci)
    _fill_asymmetric_component_fields(comp, component=component, params=params, ci=ci)
    return comp


def _apply_global_fields(entry: dict, *, params: dict, ci: dict | None) -> None:
    value, err_l, err_u = _param_tuple(params, 'ebv')
    if value or err_l or err_u:
        entry['ebvSF'] = value
        apply_astra_errors(entry, err_key='ebvSFErr', err_l=err_l, err_u=err_u)

    value, err_l, err_u = _lookup_param(params, 'd', 1)
    if value or err_l or err_u:
        entry['distMode'] = value
        apply_astra_errors(entry, err_key='distModeErr', err_l=err_l, err_u=err_u)

    if ci is None:
        return

    for ci_key, astra_val, astra_err in _GLOBAL_CI_KEYS:
        if ci_key == 'ebv' and 'ebvSF' in entry:
            continue
        value, err_up, err_down = _ci_bounds(ci, ci_key)
        if not (value or err_up or err_down):
            continue
        entry[astra_val] = value
        if astra_err:
            apply_astra_errors(
                entry,
                err_key=astra_err,
                err_l=err_down,
                err_u=err_up,
            )


def _extract_master_sed_h5py(path: str, bp: BlobPool) -> tuple[int | None, int | None]:
    try:
        with h5py.File(path, 'r') as hdf:
            if 'master/sed' not in hdf:
                return None, None
            sed = hdf['master/sed'][()]
            if sed.dtype.names:
                names = sed.dtype.names
                wl_key = 'wavelength' if 'wavelength' in names else names[0]
                fl_key = 'flux' if 'flux' in names else names[1 if len(names) > 1 else 0]
                wl = np.asarray(sed[wl_key], dtype=float).flatten()
                fl = np.asarray(sed[fl_key], dtype=float).flatten()
            else:
                arr = np.asarray(sed, dtype=float)
                if arr.ndim != 2 or arr.shape[1] < 2:
                    return None, None
                wl, fl = arr[:, 0], arr[:, 1]
    except OSError:
        return None, None

    if len(wl) == 0 or len(fl) == 0:
        return None, None
    return bp.add_doubles(list(map(float, wl))), bp.add_doubles(list(map(float, fl)))


def _extract_master_sed(
    data: dict,
    bp: BlobPool,
) -> tuple[int | None, int | None]:
    master = data.get('master')
    if not isinstance(master, dict):
        return None, None
    sed = master.get('sed')
    if sed is None:
        return None, None

    if hasattr(sed, 'dtype') and getattr(sed.dtype, 'names', None):
        names = sed.dtype.names
        wl_key = 'wavelength' if 'wavelength' in names else names[0]
        fl_key = 'flux' if 'flux' in names else names[1 if len(names) > 1 else 0]
        wl = np.asarray(sed[wl_key], dtype=float).flatten()
        fl = np.asarray(sed[fl_key], dtype=float).flatten()
    else:
        arr = np.asarray(sed, dtype=float)
        if arr.ndim != 2 or arr.shape[1] < 2:
            return None, None
        wl, fl = arr[:, 0], arr[:, 1]

    if len(wl) == 0 or len(fl) == 0:
        return None, None
    return bp.add_doubles(list(map(float, wl))), bp.add_doubles(list(map(float, fl)))


def _merge_observed(
    entry: dict,
    *,
    observed_points: list[dict] | None,
    file_observed: list[dict] | None = None,
) -> None:
    combined = list(file_observed or []) + list(observed_points or [])
    if not combined:
        return
    existing = list(entry.get('observed') or [])
    seen = {(p.get('passband'), p.get('system'), p.get('l')) for p in existing}
    for point in combined:
        key = (point.get('passband'), point.get('system'), point.get('l'))
        if key in seen:
            continue
        existing.append(point)
        seen.add(key)
    if existing:
        entry['observed'] = existing


def sed_model_from_analysis(
    analysis: Analysis,
    bp: BlobPool,
    *,
    external_id: str,
    observed_points: list[dict] | None = None,
) -> dict | None:
    """Build a full ASTRA sedModel dict from an AOTS SED-fit Analysis."""
    path = analysis.datafile.path
    if not path:
        return None

    data: dict = {}
    try:
        data = read2dict(path)
    except Exception:
        pass

    is_isis = is_isis_sed_hdf5_layout(data) if data else bool(_read_flat_ci(path))
    ci: dict | None = None
    params: dict = {}

    if is_isis:
        flat_ci = _read_flat_ci(path)
        ci = flat_ci or (_get_ci_group(data) if data else None)
        try:
            params = get_parameters(data) if data else {}
        except Exception:
            params = {}
        if not params and flat_ci:
            params = _homogenised_params_from_flat_ci(flat_ci)
    elif data:
        params = get_parameters_generic(data)
        ci = _get_ci_group(data) if data else None
    else:
        flat_ci = _read_flat_ci(path)
        if not flat_ci:
            return None
        ci = flat_ci
        params = _homogenised_params_from_flat_ci(flat_ci)

    if not params and not ci:
        return None

    object_name = analysis.name or ''
    if is_isis and data:
        try:
            object_name, _ra, _dec, _method, _note, _ref, _atype = basic_info_special_sedfit(data)
        except Exception:
            info_name, _ra, _dec = _read_sed_info(path)
            if info_name:
                object_name = info_name
    elif data:
        try:
            object_name, _ra, _dec, _method, _note, _ref, _atype = basic_info_generic(data)
        except Exception:
            object_name = str(data.get('systemname') or object_name)

    num_components = _count_components(params, ci)
    components = [
        _build_component(idx, params=params, ci=ci)
        for idx in range(1, num_components + 1)
    ]

    entry: dict = {
        'id': external_id,
        'isBestFit': analysis.is_best_fit,
        'numComponents': num_components,
        'objectName': object_name,
        'components': components,
    }

    _apply_global_fields(entry, params=params, ci=ci)

    wl_blob, flux_blob = None, None
    if data:
        wl_blob, flux_blob = _extract_master_sed(data, bp)
        if wl_blob is None or flux_blob is None:
            wl_blob, flux_blob = _extract_model_tmap(data, bp)
    if wl_blob is None or flux_blob is None:
        wl_blob, flux_blob = _extract_master_sed_h5py(path, bp)
    if wl_blob is not None and flux_blob is not None:
        entry['b_modelWl'] = wl_blob
        entry['b_modelFlux'] = flux_blob

    _merge_observed(
        entry,
        observed_points=observed_points,
        file_observed=_observed_from_data(data) if data else None,
    )
    return entry
