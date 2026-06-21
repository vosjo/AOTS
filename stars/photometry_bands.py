"""Central registry for photometric passbands and survey metadata."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

JOHNSON_B_ZEROPOINT = 0.0632573  # erg/s/cm²/Å (fluxcalib.dat)


@dataclass(frozen=True)
class PhotometryBand:
    id: str
    survey: str
    wavelength_angstrom: float
    zeropoint: float
    csv_mag: str | None = None
    csv_err: str | None = None
    vizier_catalog: str | None = None
    vizier_column: str | None = None
    vizier_err_column: str | None = None
    vizier_fetch: bool = True
    legacy: bool = False


def _band(
    band_id: str,
    survey: str,
    wavelength: float,
    zeropoint: float,
    *,
    csv_mag: str | None = None,
    csv_err: str | None = None,
    vizier_catalog: str | None = None,
    vizier_column: str | None = None,
    vizier_err_column: str | None = None,
    vizier_fetch: bool = True,
    legacy: bool = False,
) -> PhotometryBand:
    return PhotometryBand(
        id=band_id,
        survey=survey,
        wavelength_angstrom=wavelength,
        zeropoint=zeropoint,
        csv_mag=csv_mag,
        csv_err=csv_err,
        vizier_catalog=vizier_catalog,
        vizier_column=vizier_column,
        vizier_err_column=vizier_err_column,
        vizier_fetch=vizier_fetch,
        legacy=legacy,
    )


_BANDS: tuple[PhotometryBand, ...] = (
    _band(
        'GAIA3.G', 'GAIA3', 5822.39, 2.5e-9,
        csv_mag='phot_g_mean_mag', csv_err='phot_g_mean_magerr',
        vizier_catalog='I/355/gaiadr3', vizier_column='Gmag', vizier_err_column='e_Gmag',
        vizier_fetch=False,
    ),
    _band(
        'GAIA3.BP', 'GAIA3', 5035.75, 4.08e-9,
        csv_mag='phot_bp_mean_mag', csv_err='phot_bp_mean_magerr',
        vizier_catalog='I/355/gaiadr3', vizier_column='BPmag', vizier_err_column='e_BPmag',
        vizier_fetch=False,
    ),
    _band(
        'GAIA3.RP', 'GAIA3', 7619.96, 1.27e-9,
        csv_mag='phot_rp_mean_mag', csv_err='phot_rp_mean_magerr',
        vizier_catalog='I/355/gaiadr3', vizier_column='RPmag', vizier_err_column='e_RPmag',
        vizier_fetch=False,
    ),
    _band('GAIA3.RVS', 'GAIA3', 8578.16, 9.04e-10, legacy=True),
    _band('GAIA2.G', 'GAIA2', 6230, 2.46973e-09, legacy=True),
    _band('GAIA2.BP', 'GAIA2', 5050, 4.0145e-09, legacy=True),
    _band('GAIA2.RP', 'GAIA2', 7730, 1.28701e-09, legacy=True),
    _band(
        '2MASS.J', '2MASS', 12393, 3.11048e-10,
        csv_mag='Jmag', csv_err='Jmagerr',
        vizier_catalog='II/246/out', vizier_column='Jmag', vizier_err_column='e_Jmag',
    ),
    _band(
        '2MASS.H', '2MASS', 16494, 1.13535e-10,
        csv_mag='Hmag', csv_err='Hmagerr',
        vizier_catalog='II/246/out', vizier_column='Hmag', vizier_err_column='e_Hmag',
    ),
    _band(
        '2MASS.K', '2MASS', 21638, 4.27871e-11,
        csv_mag='Kmag', csv_err='Kmagerr',
        vizier_catalog='II/246/out', vizier_column='Kmag', vizier_err_column='e_Kmag',
    ),
    _band(
        'WISE.W1', 'WISE', 33526, 8.1787e-12,
        csv_mag='W1mag', csv_err='W1magerr',
        vizier_catalog='II/328/allwise', vizier_column='W1mag', vizier_err_column='e_W1mag',
    ),
    _band(
        'WISE.W2', 'WISE', 46028, 2.415e-12,
        csv_mag='W2mag', csv_err='W2magerr',
        vizier_catalog='II/328/allwise', vizier_column='W2mag', vizier_err_column='e_W2mag',
    ),
    _band(
        'WISE.W3', 'WISE', 115608, 6.5151e-14,
        csv_mag='W3mag', csv_err='W3magerr',
        vizier_catalog='II/328/allwise', vizier_column='W3mag', vizier_err_column='e_W3mag',
    ),
    _band(
        'WISE.W4', 'WISE', 220883, 5.0901e-15,
        csv_mag='W4mag', csv_err='W4magerr',
        vizier_catalog='II/328/allwise', vizier_column='W4mag', vizier_err_column='e_W4mag',
    ),
    _band(
        'GALEX.FUV', 'GALEX', 1535, 4.72496e-08,
        csv_mag='FUV', csv_err='FUVerr',
        vizier_catalog='II/312/ais', vizier_column='FUV', vizier_err_column='e_FUV',
    ),
    _band(
        'GALEX.NUV', 'GALEX', 2300, 2.21466e-08,
        csv_mag='NUV', csv_err='NUVerr',
        vizier_catalog='II/312/ais', vizier_column='NUV', vizier_err_column='e_NUV',
    ),
    _band(
        'SKYMAP.U', 'SKYMAP', 3490, 8.93655e-09,
        csv_mag='Umag', csv_err='Umagerr',
        vizier_catalog='V/145/sky2kv5', vizier_column='Umag', vizier_err_column='e_Umag',
    ),
    _band(
        'SKYMAP.V', 'SKYMAP', 3840, 7.38173e-09,
        csv_mag='Vmag', csv_err='Vmagerr',
        vizier_catalog='V/145/sky2kv5', vizier_column='Vmag', vizier_err_column='e_Vmag',
    ),
    _band(
        'SKYMAP.B', 'SKYMAP', 4400, JOHNSON_B_ZEROPOINT,
        csv_mag='Bmag', csv_err='Bmagerr',
        vizier_catalog='V/145/sky2kv5', vizier_column='Bmag', vizier_err_column='e_Bmag',
    ),
    _band('SKYMAP.G', 'SKYMAP', 5100, 4.18485e-09, legacy=True),
    _band('SKYMAP.R', 'SKYMAP', 6170, 2.85924e-09, legacy=True),
    _band('SKYMAP.I', 'SKYMAP', 7790, 1.79368e-09, legacy=True),
    _band('SKYMAP.Z', 'SKYMAP', 9160, 1.29727e-09, legacy=True),
    _band(
        'APASS.B', 'APASS', 4303, 6.40615e-09,
        csv_mag='APBmag', csv_err='APBmagerr',
        vizier_catalog='II/336/apass9', vizier_column="Bmag", vizier_err_column='e_Bmag',
    ),
    _band(
        'APASS.V', 'APASS', 5437, 3.66992e-09,
        csv_mag='APVmag', csv_err='APVmagerr',
        vizier_catalog='II/336/apass9', vizier_column='Vmag', vizier_err_column='e_Vmag',
    ),
    _band(
        'APASS.G', 'APASS', 4718, 4.92257e-09,
        csv_mag='APGmag', csv_err='APGmagerr',
        vizier_catalog='II/336/apass9', vizier_column="g'mag", vizier_err_column="e_g'mag",
    ),
    _band(
        'APASS.R', 'APASS', 6185, 2.85425e-09,
        csv_mag='APRmag', csv_err='APRmagerr',
        vizier_catalog='II/336/apass9', vizier_column="r'mag", vizier_err_column="e_r'mag",
    ),
    _band(
        'APASS.I', 'APASS', 7499, 1.94038e-09,
        csv_mag='APImag', csv_err='APImagerr',
        vizier_catalog='II/336/apass9', vizier_column="i'mag", vizier_err_column="e_i'mag",
    ),
    _band(
        'SDSS.U', 'SDSS', 3478, 3.493e-9,
        csv_mag='SDSSUmag', csv_err='SDSSUmagerr',
        vizier_catalog='V/147/sdss12', vizier_column='umag', vizier_err_column='e_umag',
    ),
    _band(
        'SDSS.G', 'SDSS', 4795, 5.352e-9,
        csv_mag='SDSSGmag', csv_err='SDSSGmagerr',
        vizier_catalog='V/147/sdss12', vizier_column='gmag', vizier_err_column='e_gmag',
    ),
    _band(
        'SDSS.R', 'SDSS', 6187, 2.541e-9,
        csv_mag='SDSSRmag', csv_err='SDSSRmagerr',
        vizier_catalog='V/147/sdss12', vizier_column='rmag', vizier_err_column='e_rmag',
    ),
    _band(
        'SDSS.I', 'SDSS', 7658, 1.323e-9,
        csv_mag='SDSSImag', csv_err='SDSSImagerr',
        vizier_catalog='V/147/sdss12', vizier_column='imag', vizier_err_column='e_imag',
    ),
    _band(
        'SDSS.Z', 'SDSS', 9668, 7.097e-10,
        csv_mag='SDSSZmag', csv_err='SDSSZmagerr',
        vizier_catalog='V/147/sdss12', vizier_column='zmag', vizier_err_column='e_zmag',
    ),
    _band(
        'PANSTAR.G', 'PANSTAR', 4810, 4.704969e-09,
        csv_mag='PANGmag', csv_err='PANGmagerr',
        vizier_catalog='II/349/ps1', vizier_column='gmag', vizier_err_column='e_gmag',
    ),
    _band(
        'PANSTAR.R', 'PANSTAR', 6170, 2.859411e-09,
        csv_mag='PANRmag', csv_err='PANRmagerr',
        vizier_catalog='II/349/ps1', vizier_column='rmag', vizier_err_column='e_rmag',
    ),
    _band(
        'PANSTAR.I', 'PANSTAR', 7520, 1.924913e-09,
        csv_mag='PANImag', csv_err='PANImagerr',
        vizier_catalog='II/349/ps1', vizier_column='imag', vizier_err_column='e_imag',
    ),
    _band(
        'PANSTAR.Z', 'PANSTAR', 8660, 1.451480e-09,
        csv_mag='PANZmag', csv_err='PANZmagerr',
        vizier_catalog='II/349/ps1', vizier_column='zmag', vizier_err_column='e_zmag',
    ),
    _band(
        'PANSTAR.Y', 'PANSTAR', 9620, 1.176242e-09,
        csv_mag='PANYmag', csv_err='PANYmagerr',
        vizier_catalog='II/349/ps1', vizier_column='ymag', vizier_err_column='e_ymag',
    ),
)

ALL_BANDS: dict[str, PhotometryBand] = {band.id: band for band in _BANDS}

PASSBANDS: list[str] = [band.id for band in _BANDS if not band.legacy]

GAIA_PHOTOMETRY_BANDS: tuple[str, ...] = ('GAIA3.G', 'GAIA3.BP', 'GAIA3.RP')

BAND_WAVELENGTHS: dict[str, float] = {
    band.id: band.wavelength_angstrom for band in _BANDS
}

ZEROPOINTS: dict[str, float] = {band.id: band.zeropoint for band in _BANDS}

CSV_MAG_BY_BAND: dict[str, str] = {
    band.id: band.csv_mag for band in _BANDS if band.csv_mag
}

CSV_ERR_BY_BAND: dict[str, str] = {
    band.id: band.csv_err for band in _BANDS if band.csv_err
}

CSV_MAG_TO_BAND: dict[str, str] = {band.csv_mag: band.id for band in _BANDS if band.csv_mag}

SURVEY_PLOT_COLORS: dict[str, str] = {
    '2MASS': 'black',
    'WISE': 'gray',
    'STROMGREN': 'olive',
    'SDSS': 'olive',
    'GAIA2': 'maroon',
    'GAIA3': 'maroon',
    'APASS': 'gold',
    'GALEX': 'powderblue',
    'PANSTAR': 'green',
    'SKYMAP': 'red',
}

# Backward-compatible flat lists aligned with PASSBANDS order.
photnames: list[str] = [CSV_MAG_BY_BAND[band_id] for band_id in PASSBANDS]
errs: list[str] = [CSV_ERR_BY_BAND[band_id] for band_id in PASSBANDS]


def build_vizier_catalogs() -> dict[str, dict[str, Any]]:
    """Build survey catalog dicts for VizieR photometry fetch (excludes GAIA3)."""
    catalogs: dict[str, dict[str, Any]] = {}
    for band in _BANDS:
        if band.legacy or not band.vizier_fetch:
            continue
        if not band.vizier_catalog or not band.vizier_column:
            continue
        entry = catalogs.setdefault(
            band.survey,
            {
                'simbad_id': band.vizier_catalog,
                'columns': [],
                'err_columns': [],
                'passbands': [],
                'photnames': [],
                'errs': [],
            },
        )
        entry['columns'].append(band.vizier_column)
        entry['err_columns'].append(band.vizier_err_column)
        entry['passbands'].append(band.id)
        entry['photnames'].append(band.csv_mag)
        entry['errs'].append(band.csv_err)
    return catalogs


def csv_import_bands() -> list[PhotometryBand]:
    """All bands that can be imported from CSV / manual photometry input."""
    return [band for band in _BANDS if band.csv_mag and not band.legacy]


def survey_groups() -> list[dict[str, Any]]:
    """Survey-grouped band list for API responses."""
    groups: dict[str, list[str]] = {}
    for band_id in PASSBANDS:
        survey = ALL_BANDS[band_id].survey
        groups.setdefault(survey, []).append(band_id)
    return [
        {'id': survey, 'label': survey, 'bands': bands}
        for survey, bands in groups.items()
    ]
