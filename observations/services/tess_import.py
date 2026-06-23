"""Fetch TESS light curves from MAST for a star."""

from __future__ import annotations

import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import astropy.units as u
from astropy.coordinates import SkyCoord
from astroquery.mast import Observations
from django.core.files import File

from observations.auxil.read_lightcurve import derive_lightcurve_info
from observations.models import LightCurve
from stars.models import Star

DEFAULT_SEARCH_RADIUS_ARCSEC = 2.0


@dataclass
class TessImportResult:
    status: str  # ok | no_match | partial | error
    message: str = ''
    imported: list[int] = field(default_factory=list)
    skipped_duplicates: int = 0
    failed: int = 0
    warnings: list[str] = field(default_factory=list)


def _coords_valid(star: Star) -> bool:
    return (
        star.ra is not None
        and star.dec is not None
        and star.ra >= 0
        and star.dec >= -90
    )


def _is_duplicate(lc: LightCurve) -> bool:
    return LightCurve.objects.exclude(pk=lc.pk).filter(
        project=lc.project,
        ra__range=[lc.ra - 1 / 3600.0, lc.ra + 1 / 3600.0],
        dec__range=[lc.dec - 1 / 3600.0, lc.dec + 1 / 3600.0],
        hjd=lc.hjd,
        instrument__iexact=lc.instrument,
    ).exists()


def query_tess_lc_products(star: Star, *, radius_arcsec: float = DEFAULT_SEARCH_RADIUS_ARCSEC):
    """Return unique TESS LC FITS products at the star position."""
    coord = SkyCoord(ra=star.ra * u.deg, dec=star.dec * u.deg)
    obs = Observations.query_criteria(
        coordinates=coord,
        radius=f'{radius_arcsec / 3600.0} deg',
        obs_collection='TESS',
    )
    if len(obs) == 0:
        return []

    timeseries = obs[obs['dataproduct_type'] == 'timeseries']
    if len(timeseries) == 0:
        return []

    products = Observations.get_product_list(timeseries)
    lc_products = products[
        (products['productSubGroupDescription'] == 'LC')
        & [str(fn).endswith('_lc.fits') for fn in products['productFilename']]
        & (products['productType'] == 'SCIENCE')
    ]

    seen: set[str] = set()
    unique = []
    for row in lc_products:
        filename = str(row['productFilename'])
        if filename in seen:
            continue
        seen.add(filename)
        unique.append(row)
    return unique


def _build_message(*, imported: int, skipped: int, failed: int) -> str:
    parts = []
    if imported:
        parts.append(f'Imported {imported} TESS light curve(s)')
    if skipped:
        parts.append(f'skipped {skipped} duplicate(s)')
    if failed:
        parts.append(f'{failed} failed')
    if not parts:
        return 'No TESS light curves imported.'
    return ', '.join(parts) + '.'


def import_tess_lightcurves_for_star(
    star: Star,
    *,
    radius_arcsec: float = DEFAULT_SEARCH_RADIUS_ARCSEC,
) -> TessImportResult:
    if not _coords_valid(star):
        return TessImportResult(status='error', message='Star has no valid coordinates.')

    try:
        lc_products = query_tess_lc_products(star, radius_arcsec=radius_arcsec)
    except Exception as exc:
        return TessImportResult(status='error', message=f'MAST query failed: {exc}')

    if not lc_products:
        return TessImportResult(
            status='no_match',
            message='No TESS light curves found at this position.',
        )

    imported_ids: list[int] = []
    skipped = 0
    failed = 0
    warnings: list[str] = []

    with tempfile.TemporaryDirectory() as tmp_dir:
        for row in lc_products:
            filename = str(row['productFilename'])
            lc: LightCurve | None = None
            try:
                manifest = Observations.download_products(row, download_dir=tmp_dir)
                if manifest is None or len(manifest) == 0:
                    failed += 1
                    warnings.append(f'{filename}: download returned no files')
                    continue

                local_path = Path(str(manifest['Local Path'][0]))
                if not local_path.is_file():
                    failed += 1
                    warnings.append(f'{filename}: downloaded file missing')
                    continue

                lc = LightCurve(project=star.project, star=star)
                with open(local_path, 'rb') as handle:
                    lc.lcfile.save(filename, File(handle), save=True)
                derive_lightcurve_info(lc.pk)
                lc.refresh_from_db()

                if _is_duplicate(lc):
                    lc.lcfile.delete(save=False)
                    lc.delete()
                    skipped += 1
                    continue

                imported_ids.append(lc.pk)
            except Exception as exc:
                failed += 1
                warnings.append(f'{filename}: {exc}')
                if lc is not None and lc.pk:
                    try:
                        if lc.lcfile:
                            lc.lcfile.delete(save=False)
                        lc.delete()
                    except OSError:
                        pass

    imported_count = len(imported_ids)
    if imported_count and (failed or skipped):
        status = 'partial'
    elif imported_count:
        status = 'ok'
    elif skipped and not failed:
        status = 'partial'
    elif failed:
        status = 'error'
    else:
        status = 'no_match'

    return TessImportResult(
        status=status,
        message=_build_message(imported=imported_count, skipped=skipped, failed=failed),
        imported=imported_ids,
        skipped_duplicates=skipped,
        failed=failed,
        warnings=warnings,
    )


def accumulate_tess_bulk_summary(summary: dict, star: Star, result: TessImportResult) -> None:
    summary['imported_lightcurves'] += len(result.imported)
    summary['skipped_duplicates'] += result.skipped_duplicates
    if result.status == 'error':
        summary['failed'] += 1
        summary['errors'].append({
            'star_pk': star.pk,
            'star_name': star.name,
            'message': result.message,
        })
    elif result.status == 'no_match':
        summary['no_match'] += 1
    elif result.status == 'partial':
        summary['partial'] += 1
    else:
        summary['ok'] += 1
