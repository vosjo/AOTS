from django.test import SimpleTestCase
import numpy as np

from analysis.auxil.fileio import read2dict
from analysis.auxil.rv_hdf5 import write_rv_curve_v2
from interop.rv_export import (
    aots_fit_params_to_astra,
    derive_astra_phi,
    rv_fits_from_data,
    rv_points_from_data,
)
from interop.rv_time import astra_time_json, bjd_to_mjd


class RvExportTests(SimpleTestCase):
    def test_astra_time_json_has_scale(self):
        t = astra_time_json(2458000.0)
        self.assertEqual(t['scale'], 'BJD')
        self.assertEqual(t['val'], 2458000.0)
        self.assertEqual(t['bjd'], 2458000.0)
        self.assertAlmostEqual(t['mjd'], bjd_to_mjd(2458000.0))

    def test_derive_astra_phi_from_t0(self):
        t_ref = 2458000.0
        t0 = 2458005.0
        period = 10.0
        phi = derive_astra_phi(t_ref=t_ref, t0=t0, period=period, eccentric=False)
        self.assertAlmostEqual(phi, 0.5)

    def test_fit_params_from_astropy_tables(self):
        import os
        import tempfile

        fd, path = tempfile.mkstemp(suffix='.h5')
        os.close(fd)
        try:
            write_rv_curve_v2(
                path,
                measurements={
                    'time': np.array([2458000.0, 2458010.0]),
                    'rv': np.array([-10.0, -8.0]),
                    'err_formal': np.array([0.5, 0.5]),
                },
                fits=[{
                    'id': 'fit-a',
                    'is_best_fit': True,
                    'parameters': {
                        'k': (100.0, 5.0, 5.0, 'km/s'),
                        'p': (10.5, 0.1, 0.1, 'd'),
                        'v0': (12.0, 0.5, 0.5, 'km/s'),
                        't0': (2458000.0, 0.1, 0.1, 'd'),
                    },
                }],
            )
            data = read2dict(path)
            points = rv_points_from_data(data)
            self.assertEqual(len(points), 2)
            self.assertEqual(points[0]['time']['scale'], 'BJD')
            self.assertEqual(points[0]['time']['bjd'], 2458000.0)
            self.assertAlmostEqual(points[0]['time']['mjd'], bjd_to_mjd(2458000.0))

            fits = rv_fits_from_data(data)
            self.assertEqual(len(fits), 1)
            fit = fits[0]
            self.assertAlmostEqual(fit['K'], 100.0)
            self.assertAlmostEqual(fit['KErr'], 5.0)
            self.assertAlmostEqual(fit['period'], 10.5)
            self.assertAlmostEqual(fit['gamma'], 12.0)
            self.assertAlmostEqual(fit['t0'], 2458000.0)
            self.assertAlmostEqual(fit['phi'], 0.0)
            self.assertAlmostEqual(fit['tRefBJD'], 2458000.0)
            self.assertAlmostEqual(fit['tRefMJD'], bjd_to_mjd(2458000.0))
        finally:
            os.unlink(path)

    def test_t00_parameter_name_exported_as_t0(self):
        params = {
            't00': {'value': 2458123.5, 'err_l': 0.2, 'err_u': 0.2},
            'p': {'value': 12.3, 'err_l': 0.01, 'err_u': 0.01},
        }
        out = aots_fit_params_to_astra(params)
        self.assertAlmostEqual(out['t0'], 2458123.5)
        self.assertAlmostEqual(out['period'], 12.3)

    def test_mjd_epochs_export_with_positive_mjd(self):
        import os
        import tempfile

        fd, path = tempfile.mkstemp(suffix='.h5')
        os.close(fd)
        try:
            write_rv_curve_v2(
                path,
                measurements={
                    'time': np.array([58000.0, 58010.0]),
                    'rv': np.array([-10.0, -8.0]),
                    'err_formal': np.array([0.5, 0.5]),
                },
                fits=[],
            )
            data = read2dict(path)
            points = rv_points_from_data(data, hdf5_path=path)
            self.assertEqual(points[0]['time']['scale'], 'MJD')
            self.assertAlmostEqual(points[0]['time']['mjd'], 58000.0)
            self.assertGreater(points[0]['time']['bjd'], 2_400_000.0)
        finally:
            os.unlink(path)

    def test_aots_fit_params_to_astra_direct(self):
        params = {
            'k': {'value': 42.0, 'err_l': 1.0, 'err_u': 3.0},
            'p': {'value': 3.14, 'err_l': 0.01, 'err_u': 0.01},
            'phi': {'value': 0.25, 'err_l': 0.02, 'err_u': 0.04},
        }
        out = aots_fit_params_to_astra(params)
        self.assertAlmostEqual(out['K'], 42.0)
        self.assertAlmostEqual(out['KErr'], 2.0)
        self.assertAlmostEqual(out['KErrUp'], 3.0)
        self.assertAlmostEqual(out['KErrDown'], 1.0)
        self.assertAlmostEqual(out['period'], 3.14)
        self.assertNotIn('periodErrUp', out)
        self.assertAlmostEqual(out['phi'], 0.25)
        self.assertAlmostEqual(out['phiErrUp'], 0.04)
        self.assertAlmostEqual(out['phiErrDown'], 0.02)

    def test_legacy_data_observations_layout(self):
        import os
        import tempfile

        import h5py

        from interop.rv_export import rv_points_from_hdf5_file

        fd, path = tempfile.mkstemp(suffix='.h5')
        os.close(fd)
        try:
            with h5py.File(path, 'w') as hdf:
                hdf.attrs['type'] = 'RC'
                data = hdf.create_group('DATA')
                dtype = np.dtype([('BJD', 'f8'), ('RV', 'f8'), ('RV_err', 'f8')])
                arr = np.array([(2458000., -10., 0.5), (2458010., -8., 0.5)], dtype=dtype)
                ds = data.create_dataset('epochs', data=arr)
                ds.attrs['xpar'] = 'BJD'
                ds.attrs['ypar'] = 'RV'
                ds.attrs['datatype'] = 'discrete'
            points = rv_points_from_hdf5_file(path)
            self.assertEqual(len(points), 2)
            self.assertEqual(points[0]['time']['scale'], 'BJD')
        finally:
            os.unlink(path)
