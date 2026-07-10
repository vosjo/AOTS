import os
import tempfile

import h5py
import numpy as np
from django.test import TestCase

from analysis.categories import AnalysisCategory
from analysis.models import Analysis
from interop.astra_package import read_astra_package
from interop.blob_pool import BlobPool, BlobReader
from interop.export_service import export_astra_package
from interop.import_service import import_astra_package
from interop.sed_export import sed_model_from_analysis
from stars.models import Project
from stars.services import star_io


def _write_synthetic_sed_hdf5(path: str, *, star_name: str = 'HD 12345') -> None:
    with h5py.File(path, 'w') as hdf:
        hdf.attrs['type'] = 'SF'
        info = hdf.create_group('info')
        info.create_dataset('oname', data=star_name)
        info.create_dataset('jradeg', data=120.5)
        info.create_dataset('jdedeg', data=-15.25)

        ci = hdf.create_group('results').create_group('iminimize').create_group('CI')
        for key, value, lower, upper in (
            ('ebv', 0.05, 0.03, 0.07),
            ('teff', 8500.0, 8200.0, 8800.0),
            ('logg', 4.2, 4.0, 4.4),
            ('z', -0.2, -0.35, -0.05),
            ('vmicro', 2.0, 1.0, 3.0),
            ('rad', 2.5, 2.2, 2.8),
            ('rad_med', 2.45, 2.15, 2.75),
            ('L', 50.0, 45.0, 55.0),
            ('chi2r', 1.15, 1.15, 1.15),
        ):
            ci.create_dataset(key, data=value)
            ci.create_dataset(f'{key}_l', data=lower)
            ci.create_dataset(f'{key}_u', data=upper)

        wl = np.linspace(3000.0, 10000.0, 50)
        flux = np.linspace(1.0, 0.5, 50)
        dtype = np.dtype([('wavelength', 'f8'), ('flux', 'f8')])
        hdf.create_group('master').create_dataset(
            'sed',
            data=np.array(list(zip(wl, flux)), dtype=dtype),
        )


class SedExportTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='SEDExport', description='')
        self.star = star_io.create_star(
            name='SED Star',
            project=self.project,
            ra=120.5,
            dec=-15.25,
        )
        self.star.photometry_set.create(
            band='GAIA3.G',
            measurement=10.5,
            error=0.02,
            unit='mag',
            source='Gaia DR3',
        )

    def test_sed_model_from_analysis_maps_ci_and_curve(self):
        fd, path = tempfile.mkstemp(suffix='.h5')
        os.close(fd)
        _write_synthetic_sed_hdf5(path)

        analysis = Analysis.objects.create(
            project=self.project,
            star=self.star,
            name='SED fit test',
            category=AnalysisCategory.SED_FIT,
            is_best_fit=True,
        )
        with open(path, 'rb') as fh:
            analysis.datafile.save('sed.h5', fh, save=True)

        bp = BlobPool()
        model = sed_model_from_analysis(
            analysis,
            bp,
            external_id='sed-fit-1',
            observed_points=[{
                'passband': 'GAIA3.G',
                'system': 'Gaia DR3',
                'mag': 10.5,
                'magErr': 0.02,
                'type': 'magnitude',
            }],
        )
        os.remove(path)

        self.assertIsNotNone(model)
        assert model is not None
        self.assertEqual(model['id'], 'sed-fit-1')
        self.assertTrue(model['isBestFit'])
        self.assertEqual(model['numComponents'], 1)
        self.assertAlmostEqual(model['ebvSF'], 0.05)
        self.assertAlmostEqual(model['chi2r'], 1.15)

        comp = model['components'][0]
        self.assertEqual(comp['idx'], 1)
        self.assertAlmostEqual(comp['teff'], 8500.0)
        self.assertAlmostEqual(comp['teff_eu'], 300.0)
        self.assertAlmostEqual(comp['teff_ed'], 300.0)
        self.assertAlmostEqual(comp['logg'], 4.2)
        self.assertAlmostEqual(comp['z'], -0.2)
        self.assertAlmostEqual(comp['xi'], 2.0)
        self.assertAlmostEqual(comp['R']['v'], 2.5)
        self.assertAlmostEqual(comp['R_med']['v'], 2.45)
        self.assertAlmostEqual(comp['L']['v'], 50.0)

        self.assertIn('b_modelWl', model)
        self.assertIn('b_modelFlux', model)
        reader = BlobReader(bp.bytes, bp.directory)
        wl = reader.get_doubles(model['b_modelWl'])
        flux = reader.get_doubles(model['b_modelFlux'])
        self.assertEqual(len(wl), 50)
        self.assertEqual(len(flux), 50)
        self.assertAlmostEqual(wl[0], 3000.0)

        self.assertEqual(len(model['observed']), 1)
        self.assertEqual(model['observed'][0]['passband'], 'GAIA3.G')

    def test_sed_roundtrip_import_export(self):
        fd, path = tempfile.mkstemp(suffix='.h5')
        os.close(fd)
        _write_synthetic_sed_hdf5(path)

        analysis = Analysis.objects.create(
            project=self.project,
            star=self.star,
            name='SED roundtrip',
            category=AnalysisCategory.SED_FIT,
            is_best_fit=True,
        )
        with open(path, 'rb') as fh:
            analysis.datafile.save('sed-roundtrip.h5', fh, save=True)
        os.remove(path)

        exported = export_astra_package(self.project, [self.star.pk])
        pkg = read_astra_package(exported)
        sed_models = pkg.stars[0]['photometry']['sedModels']
        fit_models = [m for m in sed_models if not str(m.get('id', '')).endswith('-photometry')]
        self.assertEqual(len(fit_models), 1)
        fit = fit_models[0]
        self.assertIn('components', fit)
        self.assertIn('b_modelWl', fit)
        self.assertGreater(len(fit.get('observed') or []), 0)

        import_astra_package(self.project, exported)
        reimported = Analysis.objects.filter(
            star=self.star,
            category=AnalysisCategory.SED_FIT,
        ).order_by('-pk').first()
        self.assertIsNotNone(reimported)
        with h5py.File(reimported.datafile.path, 'r') as hdf:
            ci = hdf['results/iminimize/CI']
            self.assertAlmostEqual(float(ci['teff'][()]), 8500.0)
            self.assertAlmostEqual(float(ci['ebv'][()]), 0.05)
            self.assertIn('master/sed', hdf)

    def test_generic_sedfit_layout_export(self):
        """AOTS sedfit files (DATA/MODEL/PARAMETERS) are not ISIS CI layout."""
        from pathlib import Path

        sample = Path(
            '/home/schedar/Uni/aots/src/AOTS/media/analyses/'
            'HD49798_sedfit_rTH2xL8_7R0s8xv.hdf5',
        )
        if not sample.is_file():
            self.skipTest('sample generic sedfit file not available')

        analysis = Analysis.objects.create(
            project=self.project,
            star=self.star,
            name='HD49798 SED',
            category=AnalysisCategory.SED_FIT,
            is_best_fit=True,
        )
        with sample.open('rb') as fh:
            analysis.datafile.save('hd49798_sed.h5', fh, save=True)

        bp = BlobPool()
        model = sed_model_from_analysis(analysis, bp, external_id='hd49798-sed')
        self.assertIsNotNone(model)
        assert model is not None
        self.assertIn('b_modelWl', model)
        self.assertIn('b_modelFlux', model)
        self.assertGreater(len(model.get('observed') or []), 0)
        comp = model['components'][0]
        self.assertGreater(comp.get('teff', 0), 0)
        self.assertGreater(comp.get('R', {}).get('v', 0), 0)
        reader = BlobReader(bp.bytes, bp.directory)
        self.assertGreater(len(reader.get_doubles(model['b_modelWl'])), 1000)
