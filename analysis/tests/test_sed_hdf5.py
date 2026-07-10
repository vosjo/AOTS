import os
import tempfile

import h5py
import numpy as np
from django.test import SimpleTestCase

from analysis.auxil.plot_axis_labels import FLUX_DENSITY_F_LAMBDA, WAVELENGTH_ANGSTROM, resolve_axis_labels
from analysis.auxil.sed_hdf5 import (
    SED_XUNIT,
    SED_YLABEL,
    SED_YUNIT,
    apply_sed_axis_attrs,
    ensure_sedfit_axis_metadata,
    is_generic_sedfit_hdf5,
)
from analysis.categories import AnalysisCategory


class SedHdf5MetadataTests(SimpleTestCase):
    def _write_minimal_sedfit(self, path: str) -> None:
        with h5py.File(path, 'w') as hdf:
            hdf.attrs['type'] = 'sedfit'
            data = hdf.create_group('DATA')
            data.attrs['xlabel'] = 'Wavelength (AA)'
            data.attrs['ylabel'] = 'flux'
            data.attrs['xscale'] = 'log'
            data.attrs['yscale'] = 'log'
            dtype = np.dtype([('wave', 'f8'), ('photband', 'S8'), ('flux', 'f8'), ('flux_err', 'f8')])
            data.create_dataset(
                'Obs',
                data=np.array([(5000.0, b'G', 1e-12, 1e-13)], dtype=dtype),
            )
            data['Obs'].attrs['datatype'] = 'discrete'
            data['Obs'].attrs['xpar'] = 'wave'
            data['Obs'].attrs['ypar'] = 'flux'
            model = hdf.create_group('MODEL')
            model.attrs['ylabel'] = 'Flux'
            mtype = np.dtype([('wave', 'f4'), ('flux', 'f4')])
            model.create_dataset('tmap', data=np.array([(5000.0, 1e-12)], dtype=mtype))
            model['tmap'].attrs['datatype'] = 'continuous'
            model['tmap'].attrs['xpar'] = 'wave'
            model['tmap'].attrs['ypar'] = 'flux'

    def test_apply_and_ensure_patch(self):
        fd, path = tempfile.mkstemp(suffix='.h5')
        os.close(fd)
        self._write_minimal_sedfit(path)

        with h5py.File(path, 'r') as hdf:
            self.assertTrue(is_generic_sedfit_hdf5(hdf))
            self.assertNotIn('yunit', hdf['DATA'].attrs)

        self.assertTrue(ensure_sedfit_axis_metadata(path))

        with h5py.File(path, 'r') as hdf:
            self.assertEqual(hdf['DATA'].attrs['yunit'], SED_YUNIT)
            self.assertEqual(hdf['DATA'].attrs['ylabel'], SED_YLABEL)
            self.assertEqual(hdf['DATA'].attrs['xunit'], SED_XUNIT)
            x_label, y_label = resolve_axis_labels(hdf, category=AnalysisCategory.SED_FIT)
            self.assertEqual(x_label, WAVELENGTH_ANGSTROM)
            self.assertEqual(y_label, FLUX_DENSITY_F_LAMBDA)

        os.remove(path)

    def test_apply_sed_axis_attrs_on_group(self):
        fd, path = tempfile.mkstemp(suffix='.h5')
        os.close(fd)
        with h5py.File(path, 'w') as hdf:
            grp = hdf.create_group('master')
            apply_sed_axis_attrs(grp)
            self.assertEqual(grp.attrs['yunit'], SED_YUNIT)
        os.remove(path)
