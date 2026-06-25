"""Fetch photometry from VizieR catalogs for a star."""

from __future__ import annotations

from dataclasses import dataclass

import astropy.units as u
from astropy.coordinates import SkyCoord
from astroquery.vizier import Vizier

from stars.auxil import _vizier_mag_err, catalogs


@dataclass
class VizierPhotometryResult:
    status: str  # ok | no_match | error
    message: str = ''
    bands_updated: int = 0


def import_photometry_from_vizier_for_star(star) -> VizierPhotometryResult:
    if star.ra is None or star.dec is None:
        return VizierPhotometryResult(
            status='error',
            message='Missing coordinates',
        )

    bands_updated = 0
    for content in catalogs.values():
        try:
            v = Vizier(
                catalog=content['simbad_id'],
                columns=content['columns'] + content['err_columns'],
            )
            photo = v.query_region(
                SkyCoord(ra=star.ra, dec=star.dec, unit=(u.deg, u.deg), frame='icrs'),
                radius=1 * u.arcsec,
            )
        except Exception:
            continue
        if len(photo) == 0:
            continue
        for i, column in enumerate(content['columns']):
            values = _vizier_mag_err(photo[0], column, content['err_columns'][i])
            if values is None:
                continue
            mag, err = values
            band_id = content['passbands'][i]
            star.photometry_set.filter(band=band_id).delete()
            star.photometry_set.create(
                band=band_id,
                measurement=mag,
                error=err,
                unit='mag',
            )
            bands_updated += 1

    if bands_updated == 0:
        return VizierPhotometryResult(
            status='no_match',
            message='No photometry found in VizieR',
        )
    return VizierPhotometryResult(
        status='ok',
        message='Photometry updated from VizieR',
        bands_updated=bands_updated,
    )


def accumulate_vizier_bulk_summary(summary: dict, star, result: VizierPhotometryResult) -> None:
    if result.status == 'error':
        summary['failed'] += 1
        summary['errors'].append({
            'star_pk': star.pk,
            'star_name': star.name,
            'message': result.message,
        })
    elif result.status == 'no_match':
        summary['no_match'] += 1
    else:
        summary['ok'] += 1
        summary['bands_updated_total'] += result.bands_updated
