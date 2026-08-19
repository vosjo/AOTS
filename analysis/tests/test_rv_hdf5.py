import os
import tempfile

import numpy as np
from django.test import TestCase

from analysis.auxil.fileio import read2dict
from analysis.auxil.rv_hdf5 import (
    get_best_fit_id,
    has_rv_fits,
    list_rv_fits,
    write_rv_curve_v2,
)


class RvHdf5Tests(TestCase):
    def test_write_multi_fit(self):
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
                fits=[
                    {
                        'id': 'fit-a',
                        'label': 'Fit A',
                        'is_best_fit': False,
                        'parameters': {'p': (10.0, 0.1, 0.1, 'd')},
                    },
                    {
                        'id': 'fit-b',
                        'label': 'Fit B',
                        'is_best_fit': True,
                        'parameters': {'p': (11.0, 0.2, 0.2, 'd')},
                    },
                ],
                systemname='Vega',
            )
            data = read2dict(path)
            self.assertEqual(data.get('rv_curve_format_version'), 2)
            self.assertTrue(has_rv_fits(data))
            fits = list_rv_fits(data)
            self.assertEqual(len(fits), 2)
            self.assertEqual(get_best_fit_id(data), 'fit-b')
        finally:
            os.unlink(path)
