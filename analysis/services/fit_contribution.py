"""Multi-contributor fit workflows: container lookup, append, delete, best-fit."""

from __future__ import annotations

import os
import shutil
import tempfile
import uuid
from typing import Any

from django.core.files import File
from django.db import transaction

from analysis.auxil.fileio import read2dict
from analysis.auxil.multi_fit_hdf5 import (
    append_fit,
    get_best_fit_id,
    get_fit_parameters_dict,
    has_fits,
    is_multi_fit_v2,
    list_fits,
    remove_fit,
    set_best_fit as h5_set_best_fit,
    update_fit_metadata as h5_update_fit_metadata,
    write_multi_fit_v2,
)
from analysis.auxil import process_analyses
from analysis.categories import AnalysisCategory
from analysis.models import Analysis, Parameter
from analysis.services.fit_permissions import (
    category_supports_multi_fit,
    user_can_contribute_fit,
    user_can_delete_fit,
    user_can_edit_fit,
    user_can_set_best_fit,
)
from analysis.services.fit_sync import sync_fits_from_hdf5


class FitContributionError(Exception):
    def __init__(self, message: str, *, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def _history_user(analysis: Analysis):
    if not hasattr(analysis, 'history'):
        return None
    record = analysis.history.order_by('history_date').first()
    return record.history_user if record else None


def _container_filter_kwargs(
    *,
    category: str,
    star=None,
    spectrum=None,
    lightcurve=None,
) -> dict[str, Any]:
    if category in (AnalysisCategory.RV_CURVE, AnalysisCategory.SED_FIT):
        if star is None:
            raise FitContributionError('star is required for this category')
        return {'star': star, 'category': category}
    if category == AnalysisCategory.SPECTRAL_FIT:
        if spectrum is None:
            raise FitContributionError('spectrum is required for spectral fits')
        return {'spectrum': spectrum, 'category': category}
    if category == AnalysisCategory.LIGHTCURVE_FIT:
        if lightcurve is None:
            raise FitContributionError('lightcurve is required for LC fits')
        return {'lightcurve': lightcurve, 'category': category}
    raise FitContributionError(f'Category does not support multi-fit containers: {category}')


def get_container(
    *,
    project,
    category: str,
    star=None,
    spectrum=None,
    lightcurve=None,
) -> Analysis | None:
    if not category_supports_multi_fit(category):
        return None
    lookup = _container_filter_kwargs(
        category=category, star=star, spectrum=spectrum, lightcurve=lightcurve,
    )
    return Analysis.objects.filter(project=project, **lookup).first()


def get_or_create_container(
    *,
    project,
    category: str,
    star=None,
    spectrum=None,
    lightcurve=None,
    user=None,
    initial_path: str | None = None,
    history_user_id: int | None = None,
) -> tuple[Analysis, bool]:
    """Return (container Analysis, created)."""
    if not category_supports_multi_fit(category):
        raise FitContributionError('Category does not support multi-fit containers')

    existing = get_container(
        project=project,
        category=category,
        star=star,
        spectrum=spectrum,
        lightcurve=lightcurve,
    )
    if existing:
        return existing, False

    if not initial_path or not os.path.isfile(initial_path):
        raise FitContributionError('No container exists; initial HDF5 file is required')

    with open(initial_path, 'rb') as fh:
        analysis = Analysis(
            project=project,
            star=star or (spectrum.star if spectrum else None) or (lightcurve.star if lightcurve else None),
            spectrum=spectrum,
            lightcurve=lightcurve,
            category=category,
            name=os.path.basename(initial_path),
        )
        analysis.datafile.save(os.path.basename(initial_path), File(fh), save=False)
        if history_user_id and user is None:
            from django.contrib.auth import get_user_model
            user = get_user_model().objects.filter(pk=history_user_id).first()
        if user is not None:
            analysis._history_user = user
        analysis.save()

    from analysis.services.analysis_ingestion import ingest_analysis_file
    ingest_analysis_file(analysis.pk, history_user_id=history_user_id)
    sync_fits_from_hdf5(analysis)
    return analysis, True


def _parameters_tuple_dict(data: dict) -> dict[str, tuple]:
    from analysis.auxil.read_analyses import get_parameters

    raw = get_parameters(data)
    return {
        name: (vals[0], vals[1], vals[2], vals[3])
        for name, vals in raw.items()
    }


def _fit_dict_from_legacy(data: dict, *, fit_id: str | None = None) -> dict[str, Any]:
    fit_id = fit_id or str(uuid.uuid4())
    fit: dict[str, Any] = {
        'id': fit_id,
        'label': data.get('name') or 'Fit',
        'is_best_fit': True,
        'method': '',
    }
    params = data.get('PARAMETERS')
    if isinstance(params, dict) and params:
        fit['parameters'] = _parameters_tuple_dict({'PARAMETERS': params})
    model = data.get('MODEL')
    if isinstance(model, dict) and model:
        fit['model'] = _model_series_from_block(model)
        # Prefer actual table column names (e.g. wave/flux) over DATA axis label strings.
        first_ds = next(
            (ds for ds in model.values() if hasattr(ds, 'dtype') and getattr(ds.dtype, 'names', None)),
            None,
        )
        if first_ds is not None and first_ds.dtype.names:
            fit['model_xlabel'] = first_ds.dtype.names[0]
            fit['model_ylabel'] = first_ds.dtype.names[1] if len(first_ds.dtype.names) > 1 else 'y'
        else:
            data_grp = data.get('DATA', {})
            if isinstance(data_grp, dict):
                fit['model_xlabel'] = data_grp.get('xlabel', 'x')
                fit['model_ylabel'] = data_grp.get('ylabel', 'y')
    return fit


def _model_series_from_block(model_block: dict) -> dict[str, Any]:
    import numpy as np

    series: dict[str, Any] = {}
    for name, dataset in model_block.items():
        if hasattr(dataset, 'dtype') and getattr(dataset.dtype, 'names', None):
            names = dataset.dtype.names
            xkey = names[0]
            ykey = names[1] if len(names) > 1 else names[0]
            errkey = f'{ykey}_err' if f'{ykey}_err' in names else None
            x = np.asarray(dataset[xkey], dtype=float)
            y = np.asarray(dataset[ykey], dtype=float)
            err = np.asarray(dataset[errkey], dtype=float) if errkey else None
            meta = getattr(dataset, 'meta', None) or {}
            datatype = meta.get('datatype') or 'continuous'
            if isinstance(datatype, bytes):
                datatype = datatype.decode('utf-8', errors='replace')
            label = meta.get('label')
            if isinstance(label, bytes):
                label = label.decode('utf-8', errors='replace')
            series[name] = {
                'data': (x, y, err),
                'datatype': datatype,
                'label': label,
            }
    return series


def extract_contributor_fit(upload_path: str, *, external_id: str = '') -> dict[str, Any]:
    """Build fit dict from contributor HDF5 (fit-only or legacy single-fit)."""
    data = read2dict(upload_path)
    category = None
    if is_multi_fit_v2(data):
        fits = list_fits(data)
        if not fits:
            raise FitContributionError('HDF5 has no fits to contribute')
        fit_id = fits[0]['id']
        fit_group = data.get('FITS', {}).get(fit_id, {})
        fit: dict[str, Any] = {
            'id': external_id or fit_id,
            'label': fits[0].get('label') or fit_id,
            'method': fits[0].get('method') or '',
            'external_id': external_id or fits[0].get('external_id') or '',
            'uploaded_by_user_id': fits[0].get('uploaded_by_user_id'),
            'uploaded_by_username': fits[0].get('uploaded_by_username') or '',
        }
        if isinstance(fit_group, dict):
            params = fit_group.get('PARAMETERS')
            if isinstance(params, dict) and params:
                fit['parameters'] = _parameters_tuple_dict({'PARAMETERS': params})
            model = fit_group.get('MODEL')
            if isinstance(model, dict) and model:
                fit['model'] = _model_series_from_block(model)
        return fit

    if 'PARAMETERS' in data or 'MODEL' in data:
        fit = _fit_dict_from_legacy(data, fit_id=external_id or str(uuid.uuid4()))
        if external_id:
            fit['external_id'] = external_id
        return fit

    raise FitContributionError('HDF5 does not contain fit data (PARAMETERS/MODEL or FITS/)')


def contribute_fit(
    analysis: Analysis,
    user,
    *,
    upload_path: str,
    label: str = '',
    method: str = '',
    external_id: str = '',
    set_as_best: bool = False,
    skip_permissions: bool = False,
) -> str:
    if not category_supports_multi_fit(analysis.category):
        raise FitContributionError('Analysis is not a multi-fit container category')
    if not skip_permissions and not user_can_contribute_fit(user, analysis):
        raise FitContributionError('Permission denied', status_code=403)

    fit = extract_contributor_fit(upload_path, external_id=external_id)
    if label:
        fit['label'] = label
    if method:
        fit['method'] = method
    if set_as_best:
        fit['is_best_fit'] = True

    path = analysis.datafile.path
    fit_id = append_fit(
        path,
        fit,
        uploaded_by_user_id=user.pk if user else fit.get('uploaded_by_user_id'),
        uploaded_by_username=user.get_username() if user else (fit.get('uploaded_by_username') or ''),
        set_as_best=set_as_best,
    )
    sync_fits_from_hdf5(analysis)
    if set_as_best or get_best_fit_id(analysis.get_data(), category=analysis.category) == fit_id:
        reingest_best_fit_parameters(analysis, history_user_id=user.pk)
    else:
        analysis.fit = has_fits(analysis.get_data(), category=analysis.category)
        analysis.save(update_fields=['fit'])
    return fit_id


def delete_fit_record(analysis: Analysis, fit_id: str, user) -> None:
    fit = analysis.fits.filter(fit_id=fit_id).first()
    if fit is None:
        raise FitContributionError('Fit not found', status_code=404)
    if not user_can_delete_fit(user, fit):
        raise FitContributionError('Permission denied', status_code=403)

    path = analysis.datafile.path
    if not remove_fit(path, fit_id):
        raise FitContributionError('Fit not found in HDF5', status_code=404)

    sync_fits_from_hdf5(analysis)
    reingest_best_fit_parameters(analysis, history_user_id=user.pk)


def patch_fit_metadata(
    analysis: Analysis,
    fit_id: str,
    user,
    *,
    label: str | None = None,
    method: str | None = None,
) -> None:
    fit = analysis.fits.filter(fit_id=fit_id).first()
    if fit is None:
        raise FitContributionError('Fit not found', status_code=404)
    if not user_can_edit_fit(user, fit):
        raise FitContributionError('Permission denied', status_code=403)

    if not h5_update_fit_metadata(analysis.datafile.path, fit_id, label=label, method=method):
        raise FitContributionError('Fit not found in HDF5', status_code=404)

    sync_fits_from_hdf5(analysis)


def set_container_best_fit(analysis: Analysis, fit_id: str, user) -> None:
    if not user_can_set_best_fit(user, analysis):
        raise FitContributionError('Permission denied', status_code=403)
    if not analysis.fits.filter(fit_id=fit_id).exists():
        raise FitContributionError('Fit not found', status_code=404)
    if not h5_set_best_fit(analysis.datafile.path, fit_id):
        raise FitContributionError('Fit not found in HDF5', status_code=404)

    sync_fits_from_hdf5(analysis)
    reingest_best_fit_parameters(analysis, history_user_id=user.pk)


def reingest_best_fit_parameters(analysis: Analysis, *, history_user_id: int | None = None) -> int:
    """Replace DB parameters with best-fit HDF5 parameters. Returns parameter count."""
    Parameter.objects.filter(analysis=analysis).delete()
    data = analysis.get_data()
    count = 0
    if category_supports_multi_fit(analysis.category) and is_multi_fit_v2(data, analysis.category):
        fit_id = get_best_fit_id(data, category=analysis.category)
        analysis.fit = bool(fit_id)
        if fit_id:
            count = process_analyses.create_parameters(analysis, data)
    elif data.get('PARAMETERS'):
        count = process_analyses.create_parameters(analysis, data)
        analysis.fit = True
    else:
        analysis.fit = False

    if history_user_id:
        from django.contrib.auth import get_user_model
        user = get_user_model().objects.filter(pk=history_user_id).first()
        if user is not None:
            analysis._history_user = user
    analysis.save(update_fields=['fit'])
    sync_fits_from_hdf5(analysis)
    return count


def fit_parameters_for_api(analysis: Analysis, fit_id: str | None = None) -> list[dict]:
    """Serialize HDF5 fit parameters for GET fit-parameters."""
    from analysis.parameter_labels import effective_parameter_unit, parameter_label_with_unit, unit_display_name

    data = analysis.get_data()
    pars = get_fit_parameters_dict(data, fit_id, category=analysis.category)
    rows = []
    for name, raw in pars.items():
        if isinstance(raw, dict):
            value = raw.get('value', 0)
            err_l = raw.get('err_l', 0)
            err_u = raw.get('err_u', 0)
            unit = raw.get('unit', '') or ''
        elif hasattr(raw, 'dtype') and raw.dtype.names:
            row = raw[0]
            value = float(row['value'])
            err_l = float(row['err_l'])
            err_u = float(row['err_u'])
            meta = getattr(raw, 'meta', None) or {}
            unit = str(meta.get('unit') or '')
        else:
            continue
        cname = name
        component = 0
        if name[-1] in '012' and len(name) > 1:
            component = int(name[-1])
            cname = name[:-1]
        unit_eff = effective_parameter_unit(cname, unit, from_cname=True)
        rows.append({
            'cname': cname,
            'component': component,
            'name': name,
            'value': value,
            'error_l': err_l,
            'error_u': err_u,
            'unit': unit_eff,
            'unit_display': unit_display_name(unit_eff),
            'display_label': parameter_label_with_unit(cname, unit_eff, from_cname=True),
        })
    return rows


def contribute_to_parent(
    *,
    project,
    category: str,
    user,
    upload_path: str,
    star=None,
    spectrum=None,
    lightcurve=None,
    label: str = '',
    method: str = '',
    external_id: str = '',
    set_as_best: bool = False,
    skip_permissions: bool = False,
) -> tuple[Analysis, str]:
    """Get or create container for parent object and append fit."""
    container = get_container(
        project=project,
        category=category,
        star=star,
        spectrum=spectrum,
        lightcurve=lightcurve,
    )
    if container is None:
        container, _created = get_or_create_container(
            project=project,
            category=category,
            star=star,
            spectrum=spectrum,
            lightcurve=lightcurve,
            user=user,
            initial_path=upload_path,
            history_user_id=user.pk,
        )
        fits = list_fits(container.get_data(), category=category)
        fit_id = fits[0]['id'] if fits else get_best_fit_id(container.get_data(), category=category) or ''
        return container, fit_id or ''

    fit_id = contribute_fit(
        container,
        user,
        upload_path=upload_path,
        label=label,
        method=method,
        external_id=external_id,
        set_as_best=set_as_best,
        skip_permissions=skip_permissions,
    )
    return container, fit_id
