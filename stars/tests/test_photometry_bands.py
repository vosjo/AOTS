from astropy.table import Table
from django.test import SimpleTestCase

from stars.auxil import _resolve_vizier_column, _vizier_mag_err
from stars.photometry_bands import (
    ALL_BANDS,
    CSV_MAG_BY_BAND,
    CSV_MAG_TO_BAND,
    GAIA_PHOTOMETRY_BANDS,
    PASSBANDS,
    build_vizier_catalogs,
    csv_import_bands,
)


class PhotometryBandsTests(SimpleTestCase):
    def test_passbands_have_wavelength_and_zeropoint(self):
        for band_id in PASSBANDS:
            band = ALL_BANDS[band_id]
            self.assertGreater(band.wavelength_angstrom, 0, band_id)
            self.assertGreater(band.zeropoint, 0, band_id)

    def test_passbands_count_matches_non_legacy(self):
        non_legacy = {band.id for band in ALL_BANDS.values() if not band.legacy}
        self.assertEqual(len(PASSBANDS), len(non_legacy))
        self.assertEqual(set(PASSBANDS), non_legacy)

    def test_vizier_catalogs_exclude_gaia3(self):
        catalogs = build_vizier_catalogs()
        self.assertNotIn('GAIA3', catalogs)
        for entry in catalogs.values():
            for band_id in entry['passbands']:
                self.assertFalse(band_id.startswith('GAIA3.'))

    def test_skymap_vizier_has_u_v_b_only(self):
        skymap = build_vizier_catalogs()['SKYMAP']
        self.assertEqual(
            skymap['passbands'],
            ['SKYMAP.U', 'SKYMAP.V', 'SKYMAP.B'],
        )
        self.assertEqual(skymap['columns'], ['Umag', 'Vmag', 'Bmag'])

    def test_csv_mag_names_are_unique(self):
        self.assertEqual(len(CSV_MAG_BY_BAND), len(CSV_MAG_TO_BAND))

    def test_gaia_photometry_bands(self):
        self.assertEqual(GAIA_PHOTOMETRY_BANDS, ('GAIA3.G', 'GAIA3.BP', 'GAIA3.RP'))
        for band_id in GAIA_PHOTOMETRY_BANDS:
            self.assertFalse(ALL_BANDS[band_id].vizier_fetch)

    def test_legacy_skymap_griz_not_in_passbands(self):
        for band_id in ('SKYMAP.G', 'SKYMAP.R', 'SKYMAP.I', 'SKYMAP.Z'):
            self.assertTrue(ALL_BANDS[band_id].legacy)
            self.assertNotIn(band_id, PASSBANDS)
            self.assertIn(band_id, ALL_BANDS)

    def test_csv_import_includes_gaia3(self):
        csv_band_ids = {band.id for band in csv_import_bands()}
        self.assertTrue({'GAIA3.G', 'GAIA3.BP', 'GAIA3.RP'}.issubset(csv_band_ids))


class VizierColumnResolutionTests(SimpleTestCase):
    def test_resolve_apostrophe_column_literal_name(self):
        row = Table({"g'mag": [12.3], "e_g'mag": [0.1]})[0]
        self.assertEqual(_resolve_vizier_column(row, "g'mag"), "g'mag")
        self.assertEqual(_resolve_vizier_column(row, "e_g'mag"), "e_g'mag")

    def test_resolve_apostrophe_column_legacy_underscore_name(self):
        row = Table({'g_mag': [12.3], 'e_g_mag': [0.1]})[0]
        self.assertEqual(_resolve_vizier_column(row, "g'mag"), 'g_mag')

    def test_vizier_mag_err_reads_apostrophe_columns(self):
        table = Table({"g'mag": [12.3], "e_g'mag": [0.1]})
        self.assertEqual(_vizier_mag_err(table, "g'mag", "e_g'mag"), (12.3, 0.1))

    def test_vizier_mag_err_missing_column_returns_none(self):
        table = Table({'Bmag': [12.3], 'e_Bmag': [0.1]})
        self.assertIsNone(_vizier_mag_err(table, "g'mag", "e_g'mag"))
