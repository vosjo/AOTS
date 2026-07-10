from django.test import TestCase

from analysis.categories import AnalysisCategory
from analysis.models import Analysis
from interop.astra_package import read_astra_package, write_astra_package
from interop.blob_pool import BlobPool
from interop.export_service import export_astra_package
from interop.import_service import import_astra_package
from interop.models import InteropRecord
from stars.models import Project, Star
from stars.services import star_io


class ImportExportTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='InteropTest', description='')

    def test_import_minimal_star(self):
        bp = BlobPool()
        stars = [{
            'id': 'star-uuid-1',
            'alias': 'Test Star',
            'ra': 10.5,
            'dec': 20.25,
            'spectra': [],
        }]
        raw = write_astra_package(stars, blob_pool=bp)
        batch, result = import_astra_package(self.project, raw)
        self.assertEqual(batch.status, 'completed')
        self.assertEqual(result.created_stars, 1)
        star = Star.objects.get(project=self.project, name='Test Star')
        self.assertTrue(
            InteropRecord.objects.filter(
                source=InteropRecord.SOURCE_ASTRA,
                external_id='star-uuid-1',
                object_id=star.pk,
            ).exists()
        )

    def test_import_rv_and_roundtrip_export(self):
        bp = BlobPool()
        stars = [{
            'id': 'star-rv-1',
            'alias': 'RV Star',
            'ra': 15.0,
            'dec': -10.0,
            'rv': {
                'id': 'rv-1',
                'points': [
                    {'rv': -12.0, 'errFormal': 0.5, 'time': {'bjd': 2458000.0}},
                    {'rv': -11.0, 'errFormal': 0.5, 'time': {'bjd': 2458010.0}},
                ],
                'fits': [{
                    'id': 'fit-1',
                    'isBestFit': True,
                    'K': 100.0,
                    'gamma': 5.0,
                    'period': 10.0,
                }],
            },
        }]
        raw = write_astra_package(stars, blob_pool=bp)
        import_astra_package(self.project, raw)
        star = Star.objects.get(project=self.project, name='RV Star')
        self.assertEqual(
            Analysis.objects.filter(star=star, category=AnalysisCategory.RV_CURVE).count(),
            1,
        )

        exported = export_astra_package(self.project, [star.pk])
        pkg = read_astra_package(exported)
        self.assertEqual(len(pkg.stars), 1)
        self.assertIn('rv', pkg.stars[0])
        self.assertEqual(len(pkg.stars[0]['rv']['points']), 2)
        self.assertEqual(len(pkg.stars[0]['rv']['fits']), 1)
        fit = pkg.stars[0]['rv']['fits'][0]
        self.assertIn('K', fit)
        self.assertIn('period', fit)
        point_time = pkg.stars[0]['rv']['points'][0]['time']
        self.assertEqual(point_time.get('scale'), 'BJD')
        self.assertIn('bjd', point_time)

    def test_import_rv_phi_and_asymmetric_errors(self):
        from analysis.auxil.fileio import read2dict
        from analysis.auxil.rv_hdf5 import get_fit_parameters_dict

        bp = BlobPool()
        stars = [{
            'id': 'star-rv-asym',
            'alias': 'RV Asym Star',
            'ra': 15.0,
            'dec': -10.0,
            'rv': {
                'id': 'rv-asym',
                'points': [
                    {'rv': -12.0, 'errFormal': 0.5, 'time': {'bjd': 2458000.0}},
                ],
                'fits': [{
                    'id': 'fit-asym',
                    'isBestFit': True,
                    'K': 100.0,
                    'KErr': 5.5,
                    'KErrUp': 8.0,
                    'KErrDown': 3.0,
                    'phi': 0.25,
                    'phiErr': 0.03,
                    'period': 10.0,
                    'periodErr': 0.1,
                    'gamma': 5.0,
                }],
            },
        }]
        raw = write_astra_package(stars, blob_pool=bp)
        import_astra_package(self.project, raw)
        star = Star.objects.get(project=self.project, name='RV Asym Star')
        analysis = Analysis.objects.get(star=star, category=AnalysisCategory.RV_CURVE)
        data = read2dict(analysis.datafile.path)
        params = get_fit_parameters_dict(data, 'fit-asym')
        self.assertAlmostEqual(params['phi']['value'], 0.25)
        self.assertAlmostEqual(params['k1']['err_l'], 3.0)
        self.assertAlmostEqual(params['k1']['err_u'], 8.0)

        exported = export_astra_package(self.project, [star.pk])
        pkg = read_astra_package(exported)
        fit = pkg.stars[0]['rv']['fits'][0]
        self.assertAlmostEqual(fit['phi'], 0.25)
        self.assertAlmostEqual(fit['KErrUp'], 8.0)
        self.assertAlmostEqual(fit['KErrDown'], 3.0)

    def test_export_existing_star(self):
        star = star_io.create_star(name='Export Me', project=self.project, ra=1.0, dec=2.0)
        star.photometry_set.create(
            band='GAIA3.G',
            measurement=12.5,
            error=0.01,
            unit='mag',
            source='Gaia DR3',
        )
        star.photometry_set.create(
            band='GAIA3.BP',
            measurement=13.0,
            error=0.02,
            unit='mag',
            source='Gaia DR3',
        )
        star.photometry_set.create(
            band='GAIA3.RP',
            measurement=11.5,
            error=0.02,
            unit='mag',
            source='Gaia DR3',
        )
        photo = star.photometry_set.get(band='GAIA3.G')
        raw = export_astra_package(self.project, [star.pk])
        pkg = read_astra_package(raw)
        star_json = pkg.stars[0]
        self.assertEqual(star_json['alias'], 'Export Me')
        self.assertAlmostEqual(star_json['gmag'], 12.5)
        self.assertAlmostEqual(star_json['bp'], 13.0)
        self.assertAlmostEqual(star_json['rp'], 11.5)
        self.assertAlmostEqual(star_json['bp_rp'], 1.5)
        self.assertTrue(star_json['hasGaia'])
        points = star_json['photometry']['points']
        sed_models = star_json['photometry']['sedModels']
        self.assertEqual(len(points), 3)
        carrier = next(m for m in sed_models if m['id'].endswith('-photometry'))
        self.assertEqual(len(carrier['observed']), 3)
        g_obs = next(p for p in carrier['observed'] if p['passband'] == 'GAIA3.G')
        self.assertAlmostEqual(g_obs['mag'], 12.5)
        self.assertEqual(g_obs['system'], 'Gaia DR3')
        self.assertGreater(g_obs.get('l', 0), 0)
        g_point = next(p for p in points if p['filter'] == 'GAIA3.G')
        self.assertEqual(g_point['wl'], photo.wavelength)
        self.assertEqual(g_point['instrument'], 'Gaia DR3')

    def test_export_lightcurve_astra_time_columns(self):
        import os
        import tempfile

        import numpy as np
        from astropy.io import fits

        from interop.lc_time import ASTRA_SCALE_BTJD, TESS_BTJD_ORIGIN
        from observations.models import LightCurve

        star = star_io.create_star(name='LC Star', project=self.project, ra=1.0, dec=2.0)
        native = np.array([100.0, 200.0, 300.0])
        flux = np.array([1.0, 1.01, 0.99])
        err = np.array([0.01, 0.01, 0.01])
        fd, fits_path = tempfile.mkstemp(suffix='.fits')
        os.close(fd)
        cols = [
            fits.Column(name='TIME', format='D', array=native),
            fits.Column(name='PDCSAP_FLUX', format='D', array=flux),
            fits.Column(name='PDCSAP_FLUX_ERR', format='D', array=err),
        ]
        hdu = fits.BinTableHDU.from_columns(cols)
        hdu.header['TELESCOP'] = 'TESS'
        fits.HDUList([fits.PrimaryHDU(), hdu]).writeto(fits_path, overwrite=True)

        lc = LightCurve.objects.create(
            star=star,
            project=self.project,
            telescope='TESS',
            instrument='TESS',
            passband='TESS',
        )
        with open(fits_path, 'rb') as fh:
            lc.lcfile.save('lc.fits', fh, save=True)

        raw = export_astra_package(self.project, [star.pk])
        pkg = read_astra_package(raw)
        lc_obj = pkg.stars[0]['photometry']['lightcurves']['TESS']
        reader = pkg.blob_reader()
        b_val = reader.get_doubles(lc_obj['b_val'])
        b_bjd = reader.get_doubles(lc_obj['b_bjd'])
        b_scale = reader.get_bytes(lc_obj['b_scale'])
        self.assertEqual(lc_obj['n'], 3)
        self.assertTrue(np.allclose(b_val, native))
        self.assertTrue(np.allclose(b_bjd, native + TESS_BTJD_ORIGIN))
        self.assertEqual(list(b_scale), [ASTRA_SCALE_BTJD] * 3)
        os.remove(fits_path)

