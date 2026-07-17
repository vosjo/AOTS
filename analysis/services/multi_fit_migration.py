"""Merge legacy per-user analyses into one multi-fit container per dataset."""

from __future__ import annotations

import os
import tempfile
import uuid
from typing import Any

import h5py
import numpy as np
from django.db import transaction

from analysis.auxil.multi_fit_hdf5 import (
    CATEGORY_FORMAT_ATTR,
    CATEGORY_HDF5_TYPE,
    LEGACY_FIT_ID,
    is_multi_fit_v2,
    list_fits,
    write_multi_fit_v2,
)
from analysis.categories import AnalysisCategory, uses_sed_hdf5_reader
from analysis.models import Analysis
from analysis.models.analysis_redirect import AnalysisRedirect
from analysis.services.fit_contribution import _fit_dict_from_legacy, _history_user, reingest_best_fit_parameters
from analysis.services.fit_sync import sync_fits_from_hdf5


def _group_key(analysis: Analysis, category: str) -> tuple | None:
    if category == AnalysisCategory.SPECTRAL_FIT and analysis.spectrum_id:
        return ('spectrum', analysis.spectrum_id)
    if category == AnalysisCategory.LIGHTCURVE_FIT and analysis.lightcurve_id:
        return ('lightcurve', analysis.lightcurve_id)
    if category in (AnalysisCategory.RV_CURVE, AnalysisCategory.SED_FIT) and analysis.star_id:
        return ('star', analysis.star_id)
    return None


def _uploaded_by_from_analysis(analysis: Analysis) -> tuple[int | None, str]:
    user = _history_user(analysis)
    if user is None:
        return None, ''
    return user.pk, user.get_username()


def _model_series_from_hdf5_group(grp: h5py.Group) -> dict[str, tuple]:
    series: dict[str, tuple] = {}
    for name in grp:
        item = grp[name]
        if not isinstance(item, h5py.Dataset):
            continue
        arr = item[()]
        if not hasattr(arr, 'dtype') or not getattr(arr.dtype, 'names', None):
            continue
        names = arr.dtype.names
        xkey = names[0]
        ykey = names[1] if len(names) > 1 else names[0]
        errkey = f'{ykey}_err' if f'{ykey}_err' in names else None
        x = np.asarray(arr[xkey], dtype=float)
        y = np.asarray(arr[ykey], dtype=float)
        err = np.asarray(arr[errkey], dtype=float) if errkey else None
        series[name] = (x, y, err)
    return series


def _fit_from_analysis_file(
    analysis: Analysis,
    data: dict,
    *,
    hdf5_path: str | None = None,
) -> dict[str, Any]:
    if is_multi_fit_v2(data, analysis.category):
        fits = list_fits(data, category=analysis.category)
        if not fits:
            return _fit_dict_from_legacy(data, fit_id=LEGACY_FIT_ID)
        fit_id = fits[0]['id']
        fit_group = data.get('FITS', {}).get(fit_id, {})
        uid, uname = _uploaded_by_from_analysis(analysis)
        fit: dict[str, Any] = {
            'id': str(uuid.uuid4()),
            'label': analysis.name or fits[0].get('label') or fit_id,
            'method': fits[0].get('method') or '',
            'is_best_fit': bool(analysis.is_best_fit or fits[0].get('is_best_fit')),
            'external_id': fits[0].get('external_id') or '',
            'uploaded_by_user_id': uid,
            'uploaded_by_username': uname,
        }
        legacy = _fit_dict_from_legacy({
            'PARAMETERS': fit_group.get('PARAMETERS', {}),
            'MODEL': fit_group.get('MODEL', {}),
        }, fit_id=fit['id'])
        fit.update({k: v for k, v in legacy.items() if k in ('parameters', 'model', 'model_xlabel', 'model_ylabel')})
        return fit

    if analysis.category == AnalysisCategory.SED_FIT and uses_sed_hdf5_reader(data):
        from analysis.auxil import read_analyses

        uid, uname = _uploaded_by_from_analysis(analysis)
        fit_id = str(uuid.uuid4())
        params = read_analyses.get_parameters(data)
        fit: dict[str, Any] = {
            'id': fit_id,
            'label': analysis.name or 'SED fit',
            'is_best_fit': bool(analysis.is_best_fit),
            'method': '',
            'uploaded_by_user_id': uid,
            'uploaded_by_username': uname,
            'parameters': {
                name: (vals[0], vals[1], vals[2], vals[3])
                for name, vals in params.items()
            },
            'model_xlabel': 'wavelength',
            'model_ylabel': 'flux',
        }
        if hdf5_path and os.path.isfile(hdf5_path):
            with h5py.File(hdf5_path, 'r') as hdf:
                if 'master' in hdf and 'sed' in hdf['master']:
                    arr = hdf['master']['sed'][()]
                    if hasattr(arr, 'dtype') and arr.dtype.names:
                        names = arr.dtype.names
                        xkey = 'wavelength' if 'wavelength' in names else names[0]
                        ykey = 'flux' if 'flux' in names else names[1]
                        fit['model'] = {
                            'sed': (
                                np.asarray(arr[xkey], dtype=float),
                                np.asarray(arr[ykey], dtype=float),
                                None,
                            ),
                        }
                elif 'MODEL' in hdf:
                    fit['model'] = _model_series_from_hdf5_group(hdf['MODEL'])
        return fit

    uid, uname = _uploaded_by_from_analysis(analysis)
    fit = _fit_dict_from_legacy(data, fit_id=str(uuid.uuid4()))
    fit['label'] = analysis.name or fit.get('label') or 'Fit'
    fit['is_best_fit'] = bool(analysis.is_best_fit)
    fit['uploaded_by_user_id'] = uid
    fit['uploaded_by_username'] = uname
    if hdf5_path and os.path.isfile(hdf5_path) and not fit.get('model'):
        with h5py.File(hdf5_path, 'r') as hdf:
            if 'MODEL' in hdf:
                fit['model'] = _model_series_from_hdf5_group(hdf['MODEL'])
    return fit


def _measurements_from_hdf5_path(
    path: str,
    category: str,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Read shared DATA/measurements directly from HDF5 (avoids astropy unicode conversion)."""
    if not path or not os.path.isfile(path):
        return None, None

    with h5py.File(path, 'r') as hdf:
        if 'DATA' in hdf:
            grp = hdf['DATA']
            payload: dict[str, Any] = {}
            for name in grp:
                item = grp[name]
                if isinstance(item, h5py.Dataset):
                    payload[name] = {'data': item[()], 'attrs': dict(item.attrs)}
            attrs = {k: v for k, v in grp.attrs.items()}
            return (payload or None), attrs

        if category == AnalysisCategory.SED_FIT and 'master' in hdf:
            grp = hdf['master']
            payload = {}
            for name in grp:
                item = grp[name]
                if isinstance(item, h5py.Dataset):
                    payload[name] = {'data': item[()], 'attrs': dict(item.attrs)}
            attrs = {k: v for k, v in grp.attrs.items()}
            return (payload or None), attrs

    return None, None


def merge_analysis_group(
    analyses: list[Analysis],
    *,
    category: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    if len(analyses) < 1:
        return {'skipped': True, 'reason': 'empty'}

    analyses = sorted(analyses, key=lambda a: (not a.is_best_fit, a.pk))
    container = analyses[0]
    others = analyses[1:]

    if len(analyses) == 1:
        data = container.get_data()
        if is_multi_fit_v2(data, category):
            if not dry_run:
                sync_fits_from_hdf5(container)
            return {'container_pk': container.pk, 'merged': 0, 'skipped': True}

    fits_out: list[dict[str, Any]] = []
    measurements_data = None
    data_attrs = None
    root_attrs = {}

    for analysis in analyses:
        data = analysis.get_data()
        hdf5_path = analysis.datafile.path if analysis.datafile else ''
        if measurements_data is None and hdf5_path:
            measurements_data, data_attrs = _measurements_from_hdf5_path(hdf5_path, category)
        for key in ('systemname', 'ra', 'dec', 'name', 'note', 'reference'):
            if key in data and key not in root_attrs:
                root_attrs[key] = data[key]
        fits_out.append(_fit_from_analysis_file(analysis, data, hdf5_path=hdf5_path))

    if fits_out and not any(f.get('is_best_fit') for f in fits_out):
        fits_out[0]['is_best_fit'] = True

    if dry_run:
        return {
            'container_pk': container.pk,
            'merged': len(others),
            'fit_count': len(fits_out),
            'dry_run': True,
        }

    fmt_attr = CATEGORY_FORMAT_ATTR.get(category, 'fit_format_version')
    hdf5_type = CATEGORY_HDF5_TYPE.get(category, '??')

    with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as tmp:
        tmp_path = tmp.name

    write_multi_fit_v2(
        tmp_path,
        category=category,
        hdf5_type=hdf5_type,
        measurements_data=measurements_data,
        data_group_attrs=data_attrs,
        fits=fits_out,
        systemname=str(root_attrs.get('systemname', '')),
        ra=float(root_attrs.get('ra', 0) or 0),
        dec=float(root_attrs.get('dec', 0) or 0),
        name=str(root_attrs.get('name', container.name or '')),
        note=str(root_attrs.get('note', '')),
        reference=str(root_attrs.get('reference', '')),
        root_attrs={fmt_attr: 2},
    )

    with open(tmp_path, 'rb') as fh:
        from django.core.files import File
        container.datafile.save(os.path.basename(container.datafile.name or 'merged.h5'), File(fh), save=True)
    os.unlink(tmp_path)

    container.is_best_fit = False
    container.save(update_fields=['is_best_fit'])
    sync_fits_from_hdf5(container)
    reingest_best_fit_parameters(container)

    for analysis in others:
        fit_id = ''
        synced = list_fits(container.get_data(), category=category)
        if synced:
            fit_id = synced[-1]['id']
        AnalysisRedirect.objects.update_or_create(
            old_analysis_id=analysis.pk,
            defaults={'container': container, 'fit_id': fit_id},
        )
        analysis.delete()

    return {'container_pk': container.pk, 'merged': len(others), 'fit_count': len(fits_out)}


def migrate_category_containers(
    category: str,
    *,
    project_id: int | None = None,
    dry_run: bool = False,
) -> list[dict]:
    qs = Analysis.objects.filter(category=category).exclude(datafile='')
    if project_id:
        qs = qs.filter(project_id=project_id)

    groups: dict[tuple, list[Analysis]] = {}
    for analysis in qs.iterator():
        key = _group_key(analysis, category)
        if key is None:
            continue
        groups.setdefault(key, []).append(analysis)

    results = []
    for _key, analyses in groups.items():
        with transaction.atomic():
            results.append(merge_analysis_group(analyses, category=category, dry_run=dry_run))
    return results
