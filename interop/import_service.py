"""Import ASTRA .astra packages into AOTS."""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass, field

from django.contrib.contenttypes.models import ContentType
from django.core.files import File
from django.db import transaction

from analysis.categories import AnalysisCategory
from analysis.models import Analysis
from analysis.services.analysis_ingestion import ingest_analysis_file
from analysis.models import ParameterSource
from analysis.services import parameter_io
from interop.astra_package import read_astra_package
from interop.converters import lc_fit, rv, sed, spectral_fit, spectrum, lightcurve
from interop.models import InteropImportBatch, InteropRecord
from interop.star_match import apply_identifiers, match_star
from observations.models import LightCurve, Photometry, SpecFile, Spectrum
from stars.models import Star
from stars.services import star_io


@dataclass
class ImportResult:
    created_stars: int = 0
    updated_stars: int = 0
    created_spectra: int = 0
    created_lightcurves: int = 0
    created_analyses: int = 0
    warnings: list[str] = field(default_factory=list)


def _link_record(batch, source, external_id, obj):
    ct = ContentType.objects.get_for_model(obj)
    InteropRecord.objects.update_or_create(
        source=source,
        external_id=external_id,
        content_type=ct,
        defaults={'object_id': obj.pk, 'import_batch': batch},
    )


def _create_analysis_from_path(
    project,
    star,
    path,
    category,
    *,
    batch,
    external_id,
    is_best_fit=False,
    spectrum_obj=None,
    lightcurve_obj=None,
):
    with open(path, 'rb') as fh:
        analysis = Analysis.objects.create(
            project=project,
            star=star,
            category=category,
            datafile=File(fh, name=os.path.basename(path)),
            is_best_fit=is_best_fit,
            spectrum=spectrum_obj,
            lightcurve=lightcurve_obj,
        )
    ingest_analysis_file(analysis.pk)
    if external_id:
        _link_record(batch, InteropRecord.SOURCE_ASTRA, external_id, analysis)
    return analysis


def _parameter_source(project, name='ASTRA import'):
    obj, _ = ParameterSource.objects.get_or_create(project=project, name=name, defaults={})
    return obj


def _import_photometry_point(project, star, point: dict, *, default_source: str) -> None:
    source = _parameter_source(project)
    band = point.get('passband') or point.get('filter') or point.get('band') or 'unknown'
    mag = point.get('mag')
    if mag is None:
        mag = point.get('magnitude')
    if mag is None:
        return
    instrument = point.get('system') or point.get('instrument') or default_source
    Photometry.objects.create(
        star=star,
        band=str(band),
        measurement=float(mag),
        error=float(point.get('magErr') or point.get('magnitudeErr') or point.get('error') or 0),
        unit='mag',
        wavelength=float(point.get('l') or point.get('wl') or point.get('wavelength') or 0),
        source=instrument,
    )


def _import_photometry_points(project, star, photometry_container: dict) -> None:
    seen: set[tuple[str, str]] = set()
    for key in ('sedPoints', 'points'):
        for point in photometry_container.get(key) or []:
            band = str(point.get('passband') or point.get('filter') or point.get('band') or 'unknown')
            instrument = str(point.get('system') or point.get('instrument') or 'ASTRA import')
            dedupe = (band, instrument)
            if dedupe in seen:
                continue
            seen.add(dedupe)
            _import_photometry_point(project, star, point, default_source='ASTRA import')


def import_astra_package(project, raw: bytes, *, star_names: list[str] | None = None) -> tuple[InteropImportBatch, ImportResult]:
    package = read_astra_package(raw)
    batch = InteropImportBatch.objects.create(
        project=project,
        source=InteropRecord.SOURCE_ASTRA,
        filename='import.astra',
        status='running',
    )
    result = ImportResult(warnings=list(package.warnings))
    reader = package.blob_reader()

    stars_data = package.stars
    if star_names:
        allowed = {name.lower() for name in star_names}
        stars_data = [
            s for s in stars_data
            if (s.get('alias') or '').lower() in allowed or (s.get('jname') or '').lower() in allowed
        ]

    with transaction.atomic():
        for astra_star in stars_data:
            astra_id = astra_star.get('id') or str(uuid.uuid4())
            ra = float(astra_star.get('ra') or 0)
            dec = float(astra_star.get('dec') or 0)
            name = (astra_star.get('alias') or astra_star.get('jname') or f'ASTRA-{astra_id[:8]}').strip()

            star = match_star(project, astra_star)
            if star:
                result.updated_stars += 1
            else:
                star = star_io.create_star(name=name, project=project, ra=ra, dec=dec)
                result.created_stars += 1
            apply_identifiers(star, astra_star)
            _link_record(batch, InteropRecord.SOURCE_ASTRA, astra_id, star)

            spectrum_map: dict[str, Spectrum] = {}
            for spec_obj in astra_star.get('spectra') or []:
                spec_id = spec_obj.get('id') or str(uuid.uuid4())
                fits_path = spectrum.write_spectrum_fits(spec_obj, reader)
                with open(fits_path, 'rb') as fh:
                    specfile = SpecFile.objects.create(
                        project=project,
                        specfile=File(fh, name=f'astra_{spec_id}.fits'),
                        instrument=spec_obj.get('instrument') or '',
                    )
                from observations.auxil import read_spectrum
                read_spectrum.process_specfile(specfile.pk, create_new_star=False)
                specfile.refresh_from_db()
                if specfile.spectrum_id:
                    spectrum_obj = specfile.spectrum
                    spectrum_obj.star = star
                    spectrum_obj.project = project
                    spectrum_obj.save(update_fields=['star', 'project'])
                    spectrum_map[spec_id] = spectrum_obj
                    _link_record(batch, InteropRecord.SOURCE_ASTRA, spec_id, spectrum_obj)
                    result.created_spectra += 1

                for fit in spec_obj.get('fits') or []:
                    fit_id = fit.get('id') or str(uuid.uuid4())
                    h5 = spectral_fit.build_spectral_fit_hdf5(
                        fit, reader, star_name=star.name, ra=ra, dec=dec,
                    )
                    _create_analysis_from_path(
                        project, star, h5, AnalysisCategory.SPECTRAL_FIT,
                        batch=batch, external_id=fit_id,
                        is_best_fit=bool(fit.get('isBestFit')),
                        spectrum_obj=spectrum_map.get(spec_id),
                    )
                    result.created_analyses += 1
                try:
                    os.unlink(fits_path)
                except OSError:
                    pass

            photometry = astra_star.get('photometry') or {}
            if photometry:
                _import_photometry_points(project, star, photometry)

            lc_map: dict[str, LightCurve] = {}
            for source_key, lc_obj in (photometry.get('lightcurves') or {}).items():
                lc_id = f'{astra_id}:lc:{source_key}'
                lc_path = lightcurve.write_lightcurve_fits(lc_obj, reader)
                with open(lc_path, 'rb') as fh:
                    lc = LightCurve.objects.create(
                        project=project,
                        star=star,
                        lcfile=File(fh, name=f'astra_{source_key}.fits'),
                        passband=str(source_key),
                    )
                from observations.auxil import read_lightcurve
                read_lightcurve.process_lightcurve(lc.pk)
                lc_map[source_key] = lc
                _link_record(batch, InteropRecord.SOURCE_ASTRA, lc_id, lc)
                result.created_lightcurves += 1
                try:
                    os.unlink(lc_path)
                except OSError:
                    pass

            for source_key, fits in (photometry.get('lcFits') or {}).items():
                for fit in fits or []:
                    fit_id = fit.get('id') or str(uuid.uuid4())
                    h5 = lc_fit.build_lc_fit_hdf5(
                        fit, reader, star_name=star.name, ra=ra, dec=dec,
                    )
                    _create_analysis_from_path(
                        project, star, h5, AnalysisCategory.LIGHTCURVE_FIT,
                        batch=batch, external_id=fit_id,
                        is_best_fit=bool(fit.get('isBestFit')),
                        lightcurve_obj=lc_map.get(source_key),
                    )
                    result.created_analyses += 1

            for sed_model in (photometry.get('sedModels') or []):
                sed_id = sed_model.get('id') or str(uuid.uuid4())
                h5 = sed.build_sed_hdf5(
                    sed_model, reader, star_name=star.name, ra=ra, dec=dec,
                )
                _create_analysis_from_path(
                    project, star, h5, AnalysisCategory.SED_FIT,
                    batch=batch, external_id=sed_id,
                    is_best_fit=bool(sed_model.get('isBestFit')),
                )
                result.created_analyses += 1

            rv_container = astra_star.get('rv')
            if rv_container:
                rv_id = rv_container.get('id') or f'{astra_id}:rv'
                h5 = rv.build_rv_hdf5(rv_container, star_name=star.name, ra=ra, dec=dec)
                _create_analysis_from_path(
                    project, star, h5, AnalysisCategory.RV_CURVE,
                    batch=batch, external_id=rv_id,
                )
                result.created_analyses += 1

            _import_summary_parameters(project, star, astra_star)

    batch.status = 'completed'
    batch.summary = {
        'created_stars': result.created_stars,
        'updated_stars': result.updated_stars,
        'created_spectra': result.created_spectra,
        'created_lightcurves': result.created_lightcurves,
        'created_analyses': result.created_analyses,
    }
    batch.warnings = result.warnings
    batch.save(update_fields=['status', 'summary', 'warnings'])
    return batch, result


def _import_summary_parameters(project, star, astra_star: dict) -> None:
    source = _parameter_source(project)
    summary_fields = (
        ('rvK', 'k', 1, 'km/s'),
        ('rvPeriod', 'p', 0, 'd'),
        ('teff', 'teff', 1, 'K'),
        ('logg', 'logg', 1, 'dex'),
    )
    for astra_key, name, component, unit in summary_fields:
        value = astra_star.get(astra_key)
        if value is None:
            continue
        try:
            value = float(value)
        except (TypeError, ValueError):
            continue
        if not value:
            continue
        parameter_io.create_measurement(
            star=star,
            name=name,
            component=component,
            value=value,
            error_u=0,
            error_l=0,
            unit=unit,
            parameter_source=source,
            run_after=False,
        )
    parameter_io.after_star_parameters_batch(star)
