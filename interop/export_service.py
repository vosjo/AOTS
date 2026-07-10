"""Export AOTS data to ASTRA .astra packages."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

import numpy as np
from astropy.io import fits
from django.contrib.contenttypes.models import ContentType

from analysis.auxil.fileio import read2dict
from interop.astra_errors import errors_from_aots_raw, write_astra_param
from interop.rv_export import rv_fits_from_data, rv_points_from_analysis
from interop.sed_export import sed_model_from_analysis
from analysis.categories import AnalysisCategory
from analysis.models import Analysis
from interop.astra_package import write_astra_package
from interop.blob_pool import BlobPool
from analysis.services.parameter_consensus import get_consensus_parameter
from interop.lc_time import astra_native_scale, native_time_to_bjd
from interop.models import InteropRecord
from observations.models import LightCurve, Photometry, Spectrum
from stars.models import Identifier, Star
from stars.photometry_bands import BAND_WAVELENGTHS


@dataclass
class ExportOptions:
    include_spectra: bool = True
    include_spectral_fits: bool = True
    include_photometry: bool = True
    include_lightcurves: bool = True
    include_sed_models: bool = True
    include_lc_fits: bool = True
    include_rv: bool = True
    creator_note: str = ''


def _external_id(obj, source=InteropRecord.SOURCE_ASTRA) -> str:
    ct = ContentType.objects.get_for_model(obj)
    record = InteropRecord.objects.filter(
        source=source, content_type=ct, object_id=obj.pk,
    ).first()
    if record:
        return record.external_id
    return str(uuid.uuid4())


_GAIA_BAND_ASTRA = {
    'GAIA3.G': ('gmag', 'e_gmag'),
    'GAIA3.BP': ('bp', 'e_bp'),
    'GAIA3.RP': ('rp', 'e_rp'),
}

_ASTRA_PARAMETERS = (
    ('parallax', 'plx', 'e_plx'),
    ('pmra', 'pmra', 'e_pmra'),
    ('pmdec', 'pmdec', 'e_pmdec'),
)


def _star_catalog_fields(star: Star) -> dict:
    """Map AOTS Gaia photometry/parameters to ASTRA star summary fields (CMD, summary panel)."""
    data: dict = {}
    for band, (mag_key, err_key) in _GAIA_BAND_ASTRA.items():
        photo = Photometry.objects.filter(star=star, band=band).first()
        if photo is None:
            continue
        data[mag_key] = photo.measurement
        if photo.error:
            data[err_key] = photo.error
    if 'bp' in data and 'rp' in data:
        data.setdefault('bp_rp', data['bp'] - data['rp'])
    for pname, value_key, err_key in _ASTRA_PARAMETERS:
        param = get_consensus_parameter(star=star, name=pname, component=1)
        if param is None:
            continue
        data[value_key] = param.rvalue()
        if param.error:
            data[err_key] = param.rerror()
    if data.get('gmag') or data.get('plx'):
        data['hasGaia'] = True
    return data


def _star_identifiers(star: Star) -> dict:
    data = {
        'id': _external_id(star),
        'alias': star.name,
        'ra': star.ra,
        'dec': star.dec,
    }
    for ident in Identifier.objects.filter(star=star):
        name = ident.name
        if name.startswith('TIC '):
            data['tic'] = name.replace('TIC ', '').strip()
        elif name.startswith('Gaia'):
            data['sourceId'] = name
        elif name.startswith('J') and len(name) > 10:
            data['jname'] = name
    data.update(_star_catalog_fields(star))
    return data


def _photo_wavelength(photo: Photometry) -> float:
    if photo.wavelength:
        return float(photo.wavelength)
    return float(BAND_WAVELENGTHS.get(photo.band, 0.0))


def _photo_to_sed_point(photo: Photometry) -> dict:
    """ASTRA SEDPhotometryPoint JSON (used by SED Analysis → Photometry Points)."""
    wl = _photo_wavelength(photo)
    point = {
        'passband': photo.band,
        'system': photo.source or 'AOTS',
        'mag': photo.measurement,
        'magErr': photo.error,
        'type': 'magnitude',
        'flag': 0,
    }
    if wl > 0:
        point['l'] = wl
    return point


def _photometry_sed_carrier(star: Star, photos: list[Photometry]) -> dict:
    """Minimal SED model so ASTRA seeds its Photometry Points table (no ASTRA changes)."""
    return {
        'id': f'{_external_id(star)}-photometry',
        'objectName': f'AOTS photometry ({star.name})',
        'isBestFit': True,
        'numComponents': 1,
        'observed': [_photo_to_sed_point(photo) for photo in photos],
    }


def _sed_models_have_observed(sed_models: list[dict]) -> bool:
    return any(model.get('observed') for model in sed_models)


def _column_lookup(table) -> dict[str, str]:
    names = getattr(table, 'columns', None)
    if names is None:
        return {}
    return {name.upper(): name for name in names.names}


def _lightcurve_arrays(lc: LightCurve) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, int]:
    """Return native time, BJD, flux, flux error, and ASTRA time-scale byte from FITS."""
    data = fits.getdata(lc.lcfile.path)
    columns = _column_lookup(data)
    time_key = columns.get('TIME') or columns.get('BJD')
    flux_key = columns.get('PDCSAP_FLUX') or columns.get('FLUX')
    if not time_key or not flux_key:
        raise ValueError(f'Unsupported light-curve columns in {lc.lcfile.path}')

    native = np.asarray(data[time_key], dtype=float)
    flux = np.asarray(data[flux_key], dtype=float)
    err_key = columns.get('PDCSAP_FLUX_ERR') or columns.get('FLUX_ERR')
    if err_key is not None:
        err = np.asarray(data[err_key], dtype=float)
    else:
        err = np.zeros(len(flux), dtype=float)
    if len(err) != len(flux):
        err = np.zeros(len(flux), dtype=float)
    telescope = lc.telescope or ''
    instrument = lc.instrument or ''
    fits_path = lc.lcfile.path
    bjd = native_time_to_bjd(
        native,
        telescope=telescope,
        instrument=instrument,
        fits_path=fits_path,
    )
    scale = astra_native_scale(
        native,
        telescope=telescope,
        instrument=instrument,
        fits_path=fits_path,
    )
    return native, bjd, flux, err, scale


def export_astra_package(project, star_ids: list[int], options: ExportOptions | None = None) -> bytes:
    opts = options or ExportOptions()
    bp = BlobPool()
    stars_out = []

    star_qs = Star.objects.filter(project=project, pk__in=star_ids)
    for star in star_qs:
        star_json = _star_identifiers(star)
        spectra_out = []

        if opts.include_spectra:
            for spec in Spectrum.objects.filter(star=star, project=project):
                spec_id = _external_id(spec)
                try:
                    wave, flux, header = spec.get_spectrum()
                except Exception:
                    continue
                entry = {
                    'id': spec_id,
                    'instrument': spec.instrument or '',
                    'b_wl': bp.add_doubles(list(map(float, wave.flatten()))),
                    'b_flux': bp.add_doubles(list(map(float, flux.flatten()))),
                    'fits': [],
                }
                if opts.include_spectral_fits:
                    for analysis in Analysis.objects.filter(
                        star=star, spectrum=spec, category=AnalysisCategory.SPECTRAL_FIT,
                    ):
                        fit_entry = _analysis_to_spectral_fit(analysis, bp)
                        if fit_entry:
                            entry['fits'].append(fit_entry)
                spectra_out.append(entry)

        photometry_out: dict = {
            'points': [],
            'lightcurves': {},
            'sedModels': [],
            'lcFits': {},
        }
        star_photos: list[Photometry] = []
        if opts.include_photometry:
            star_photos = list(Photometry.objects.filter(star=star))
            for photo in star_photos:
                wl = _photo_wavelength(photo)
                point = {
                    'filter': photo.band,
                    'mag': photo.measurement,
                    'magErr': photo.error,
                }
                if wl > 0:
                    point['wl'] = wl
                if photo.source:
                    point['instrument'] = photo.source
                photometry_out['points'].append(point)

        if opts.include_lightcurves:
            for lc in LightCurve.objects.filter(star=star, project=project):
                source = lc.passband or f'lc-{lc.pk}'
                lc_id = _external_id(lc)
                try:
                    native, bjd, flux, err, scale = _lightcurve_arrays(lc)
                except Exception:
                    continue
                n = len(flux)
                photometry_out['lightcurves'][source] = {
                    'n': n,
                    'b_val': bp.add_doubles(list(map(float, native.flatten()))),
                    'b_scale': bp.add_bytes(bytes([scale] * n)),
                    'b_bjd': bp.add_doubles(list(map(float, bjd.flatten()))),
                    'b_flux': bp.add_doubles(list(map(float, flux.flatten()))),
                    'b_ferr': bp.add_doubles(list(map(float, err.flatten()))),
                }
                InteropRecord.objects.get_or_create(
                    source=InteropRecord.SOURCE_ASTRA,
                    external_id=lc_id,
                    content_type=ContentType.objects.get_for_model(lc),
                    defaults={'object_id': lc.pk},
                )

        if opts.include_sed_models:
            observed_for_sed = (
                [_photo_to_sed_point(photo) for photo in star_photos]
                if star_photos
                else None
            )
            for analysis in Analysis.objects.filter(star=star, category=AnalysisCategory.SED_FIT):
                sed_entry = sed_model_from_analysis(
                    analysis,
                    bp,
                    external_id=_external_id(analysis),
                    observed_points=observed_for_sed,
                )
                if sed_entry:
                    photometry_out['sedModels'].append(sed_entry)

        if star_photos and not _sed_models_have_observed(photometry_out['sedModels']):
            photometry_out['sedModels'].append(_photometry_sed_carrier(star, star_photos))

        if opts.include_lc_fits:
            for analysis in Analysis.objects.filter(star=star, category=AnalysisCategory.LIGHTCURVE_FIT):
                source = analysis.lightcurve.passband if analysis.lightcurve_id else f'lc-fit-{analysis.pk}'
                photometry_out['lcFits'].setdefault(source, [])
                lc_entry = _analysis_to_lc_fit(analysis, bp)
                if lc_entry:
                    photometry_out['lcFits'][source].append(lc_entry)

        if opts.include_photometry or opts.include_lightcurves or opts.include_sed_models or opts.include_lc_fits:
            star_json['photometry'] = photometry_out

        if opts.include_rv:
            rv_analysis = Analysis.objects.filter(star=star, category=AnalysisCategory.RV_CURVE).first()
            if rv_analysis:
                star_json['rv'] = _analysis_to_rv(rv_analysis, bp)

        if spectra_out:
            star_json['spectra'] = spectra_out
        stars_out.append(star_json)

    return write_astra_package(
        stars_out,
        blob_pool=bp,
        creator_note=opts.creator_note,
        created_by='AOTS',
    )


def _analysis_to_spectral_fit(analysis: Analysis, bp: BlobPool) -> dict | None:
    try:
        data = read2dict(analysis.datafile.path)
    except Exception:
        return None
    model = data.get('MODEL', {}).get('model') if isinstance(data.get('MODEL'), dict) else None
    entry = {
        'id': _external_id(analysis),
        'isBestFit': analysis.is_best_fit,
    }
    if model is not None and hasattr(model, 'dtype'):
        wl = model['wavelength'] if 'wavelength' in model.dtype.names else model[model.dtype.names[0]]
        fl = model['flux'] if 'flux' in model.dtype.names else model[model.dtype.names[1]]
        entry['b_modelWl'] = bp.add_doubles(list(map(float, wl)))
        entry['b_modelFlux'] = bp.add_doubles(list(map(float, fl)))
    params = data.get('PARAMETERS', {})
    if isinstance(params, dict):
        spectral_map = {
            'teff': ('teff', 'teffErr'),
            'logg': ('logg', 'loggErr'),
            'he': ('he', 'heErr'),
            'vsini': ('vsini', 'vsiniErr'),
            'rv': ('rv', 'rvErr'),
            'metal': ('metal', 'metalErr'),
            'macro': ('macro', 'macroErr'),
            'micro': ('micro', 'microErr'),
            'z': ('metal', 'metalErr'),
        }
        for key, (val_key, err_key) in spectral_map.items():
            if key not in params:
                continue
            value, err_l, err_u = errors_from_aots_raw(params[key])
            write_astra_param(
                entry,
                value_key=val_key,
                err_key=err_key,
                value=value,
                err_l=err_l,
                err_u=err_u,
            )
    return entry


def _analysis_to_lc_fit(analysis: Analysis, bp: BlobPool) -> dict | None:
    entry = {
        'id': _external_id(analysis),
        'isBestFit': analysis.is_best_fit,
        'label': analysis.name,
    }
    try:
        data = read2dict(analysis.datafile.path)
    except Exception:
        return entry
    params = data.get('PARAMETERS', {})
    if isinstance(params, dict):
        lc_map = {
            'p': ('period', 'periodErr'),
            'q': ('q', 'qErr'),
            'incl': ('incl', 'inclErr'),
            'r1': ('r1', 'r1Err'),
            'r2': ('r2', 'r2Err'),
            'vscale': ('vscale', 'vscaleErr'),
            't1': ('t1', 't1Err'),
            't2': ('t2', 't2Err'),
            't0': ('t0BJD', 't0BJDErr'),
        }
        for key, (val_key, err_key) in lc_map.items():
            if key not in params:
                continue
            value, err_l, err_u = errors_from_aots_raw(params[key])
            write_astra_param(
                entry,
                value_key=val_key,
                err_key=err_key,
                value=value,
                err_l=err_l,
                err_u=err_u,
            )
    return entry


def _analysis_to_rv(analysis: Analysis, bp: BlobPool) -> dict:
    path = analysis.datafile.path
    data = read2dict(path)
    return {
        'id': _external_id(analysis),
        'points': rv_points_from_analysis(analysis),
        'fits': rv_fits_from_data(data, hdf5_path=path),
    }
