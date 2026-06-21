"""Fetch Gaia DR3 catalog data for a star and store photometry + parameters."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
from astroquery.vizier import Vizier

from analysis.models import ParameterSource
from analysis.services import parameter_io
from stars.photometry_bands import GAIA_PHOTOMETRY_BANDS

GAIA_DR3_SOURCE_NAME = 'Gaia DR3'
GAIA_DR3_CATALOG = 'I/355/gaiadr3'
GAIA_DR3_REFERENCE = 'https://doi.org/10.1051/0004-6361/202243940'

GAIA_VIZIER_COLUMNS = [
    'Plx', 'e_Plx', 'pmRA', 'e_pmRA', 'pmDE', 'e_pmDE',
    'Gmag', 'e_Gmag', 'BPmag', 'e_BPmag', 'RPmag', 'e_RPmag',
]

ASTROMETRY_PARAMETERS = ('parallax', 'pmra', 'pmdec')
DERIVED_PARAMETERS = ('mag', 'bp_rp', 'absolute_g_mag')
ALL_GAIA_PARAMETER_NAMES = ASTROMETRY_PARAMETERS + DERIVED_PARAMETERS

PARALLAX_MAX_ERROR_MAS = 0.1


@dataclass
class GaiaImportResult:
    status: str  # ok | no_match | partial | error
    message: str = ''
    fields_updated: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _is_valid_value(value: Any) -> bool:
    if value is None:
        return False
    if str(value) == '--':
        return False
    try:
        return not np.isnan(float(value))
    except (TypeError, ValueError):
        return False


def _float_value(value: Any) -> float:
    return float(value)


def derive_bp_rp(bpmag: float, bpmag_err: float, rpmag: float, rpmag_err: float) -> tuple[float, float]:
    """BP-RP colour and propagated uncertainty."""
    value = bpmag - rpmag
    error = float(np.sqrt(bpmag_err ** 2 + rpmag_err ** 2))
    return value, error


def derive_absolute_g_mag(
    gmag: float,
    gmag_err: float,
    parallax_mas: float,
    parallax_err_mas: float,
) -> tuple[float, float] | None:
    """
    Absolute G-band magnitude from apparent G and parallax (mas).

    Returns None when parallax is unusable (non-positive or error > 0.1 mas).
    """
    if parallax_mas <= 0:
        return None
    if parallax_err_mas > PARALLAX_MAX_ERROR_MAS:
        return None
    value = gmag + 5.0 * np.log10(parallax_mas) - 10.0
    rel_err = parallax_err_mas / parallax_mas
    error = float(np.sqrt(gmag_err ** 2 + rel_err ** 2))
    return value, error


def derive_catalog_parameters(
    *,
    gmag: float | None,
    gmag_err: float | None,
    bpmag: float | None,
    bpmag_err: float | None,
    rpmag: float | None,
    rpmag_err: float | None,
    parallax_mas: float | None,
    parallax_err_mas: float | None,
) -> dict[str, tuple[float, float, str]]:
    """Build mag / bp_rp / absolute_g_mag parameter tuples (value, error, unit)."""
    derived: dict[str, tuple[float, float, str]] = {}

    if gmag is not None and gmag_err is not None:
        derived['mag'] = (gmag, gmag_err, 'mag')

    if (
        bpmag is not None and bpmag_err is not None
        and rpmag is not None and rpmag_err is not None
    ):
        bp_rp, bp_rp_err = derive_bp_rp(bpmag, bpmag_err, rpmag, rpmag_err)
        derived['bp_rp'] = (bp_rp, bp_rp_err, 'mag')

    if (
        gmag is not None and gmag_err is not None
        and parallax_mas is not None and parallax_err_mas is not None
    ):
        abs_mag = derive_absolute_g_mag(gmag, gmag_err, parallax_mas, parallax_err_mas)
        if abs_mag is not None:
            derived['absolute_g_mag'] = (abs_mag[0], abs_mag[1], 'mag')

    return derived


def get_or_create_gaia_dr3_source(project) -> ParameterSource:
    source, _created = ParameterSource.objects.get_or_create(
        project=project,
        name=GAIA_DR3_SOURCE_NAME,
        defaults={
            'note': '3rd Gaia data release',
            'reference': GAIA_DR3_REFERENCE,
        },
    )
    return source


def _query_gaia_dr3(ra: float, dec: float):
    coord = SkyCoord(ra=ra, dec=dec, unit=(u.deg, u.deg), frame='icrs')
    vizier = Vizier(
        catalog=GAIA_DR3_CATALOG,
        columns=GAIA_VIZIER_COLUMNS,
    )
    return vizier.query_region(coord, radius=1 * u.arcsec)


def _replace_photometry_band(star, band: str, measurement: float, error: float) -> None:
    star.photometry_set.filter(band=band).delete()
    star.photometry_set.create(
        band=band,
        measurement=measurement,
        error=error,
        unit='mag',
    )


def _delete_gaia_dr3_measurements(star, source: ParameterSource, names: list[str]) -> None:
    for param in star.parameter_set.filter(
        parameter_source=source,
        name__in=names,
        average=False,
    ):
        parameter_io.delete_measurement(param, run_after=False)


def _store_parameter(
    star,
    source: ParameterSource,
    name: str,
    value: float,
    error: float,
    unit: str,
) -> None:
    parameter_io.create_measurement(
        star=star,
        parameter_source=source,
        name=name,
        component=0,
        value=value,
        error_l=error,
        error_u=error,
        unit=unit,
        run_after=False,
    )


def import_gaia_dr3_for_star(star, *, replace_existing: bool = True) -> GaiaImportResult:
    """
    Fetch Gaia DR3 data from Vizier and store photometry + catalog parameters.

    Replaces existing Gaia DR3 measurements when ``replace_existing`` is True.
    """
    if star.ra is None or star.dec is None:
        return GaiaImportResult(
            status='error',
            message='Star has no coordinates (RA/Dec required).',
        )

    try:
        gaia_data = _query_gaia_dr3(star.ra, star.dec)
    except Exception as exc:
        return GaiaImportResult(
            status='error',
            message=f'VizieR query failed: {exc}',
        )

    if not gaia_data or len(gaia_data[0]) != 1:
        return GaiaImportResult(
            status='no_match',
            message='No Gaia DR3 match within 1 arcsec.',
        )

    row = gaia_data[0][0]
    source = get_or_create_gaia_dr3_source(star.project)
    fields_updated: list[str] = []
    warnings: list[str] = []

    if replace_existing:
        _delete_gaia_dr3_measurements(star, source, list(ALL_GAIA_PARAMETER_NAMES))

    band_map = [
        ('GAIA3.G', 'Gmag', 'e_Gmag'),
        ('GAIA3.BP', 'BPmag', 'e_BPmag'),
        ('GAIA3.RP', 'RPmag', 'e_RPmag'),
    ]
    gmag = gmag_err = bpmag = bpmag_err = rpmag = rpmag_err = None

    for band, mag_col, err_col in band_map:
        if not _is_valid_value(row[mag_col]):
            continue
        mag = _float_value(row[mag_col])
        err = _float_value(row[err_col]) if _is_valid_value(row[err_col]) else 0.0
        _replace_photometry_band(star, band, mag, err)
        fields_updated.append(f'photometry:{band}')
        if band == 'GAIA3.G':
            gmag, gmag_err = mag, err
        elif band == 'GAIA3.BP':
            bpmag, bpmag_err = mag, err
        elif band == 'GAIA3.RP':
            rpmag, rpmag_err = mag, err

    parallax_mas = parallax_err_mas = None
    if _is_valid_value(row['Plx']) and _is_valid_value(row['e_Plx']):
        parallax_mas = _float_value(row['Plx'])
        parallax_err_mas = _float_value(row['e_Plx'])
        _store_parameter(star, source, 'parallax', parallax_mas, parallax_err_mas, 'mas')
        fields_updated.append('parallax')

    if _is_valid_value(row['pmRA']) and _is_valid_value(row['e_pmRA']):
        _store_parameter(
            star, source, 'pmra',
            _float_value(row['pmRA']), _float_value(row['e_pmRA']), 'mas',
        )
        fields_updated.append('pmra')

    if _is_valid_value(row['pmDE']) and _is_valid_value(row['e_pmDE']):
        _store_parameter(
            star, source, 'pmdec',
            _float_value(row['pmDE']), _float_value(row['e_pmDE']), 'mas',
        )
        fields_updated.append('pmdec')

    derived = derive_catalog_parameters(
        gmag=gmag,
        gmag_err=gmag_err,
        bpmag=bpmag,
        bpmag_err=bpmag_err,
        rpmag=rpmag,
        rpmag_err=rpmag_err,
        parallax_mas=parallax_mas,
        parallax_err_mas=parallax_err_mas,
    )
    for name, (value, error, unit) in derived.items():
        _store_parameter(star, source, name, value, error, unit)
        fields_updated.append(name)

    if (
        gmag is not None
        and parallax_mas is not None
        and 'absolute_g_mag' not in derived
    ):
        warnings.append(
            'absolute_g_mag not stored (parallax non-positive or parallax error > 0.1 mas).',
        )

    if fields_updated:
        parameter_io.after_star_parameters_batch(star)

    if not fields_updated:
        return GaiaImportResult(
            status='partial',
            message='Gaia DR3 match found but no usable fields.',
            warnings=warnings,
        )

    status = 'ok' if not warnings else 'partial'
    message = f'Gaia DR3 data updated ({len(fields_updated)} fields).'
    return GaiaImportResult(
        status=status,
        message=message,
        fields_updated=fields_updated,
        warnings=warnings,
    )
