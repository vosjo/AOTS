from django.test import SimpleTestCase
import numpy as np

from interop.lc_time import (
    ASTRA_SCALE_BTJD,
    TESS_BTJD_ORIGIN,
    astra_native_scale,
    bjd_to_native_time,
    is_btjd_native_time,
    native_time_to_bjd,
)


class LcTimeTests(SimpleTestCase):
    def test_tess_btjd_to_bjd(self):
        native = np.array([100.0, 200.0])
        self.assertTrue(is_btjd_native_time(native, telescope='TESS'))
        bjd = native_time_to_bjd(native, telescope='TESS')
        self.assertAlmostEqual(bjd[0], TESS_BTJD_ORIGIN + 100.0)
        roundtrip = bjd_to_native_time(bjd)
        self.assertTrue(np.allclose(roundtrip, native))

    def test_astra_native_scale_btjd(self):
        native = np.array([100.0, 200.0])
        self.assertEqual(astra_native_scale(native, telescope='TESS'), ASTRA_SCALE_BTJD)

    def test_bjd_left_unchanged(self):
        bjd = np.array([2_459_000.0, 2_459_010.0])
        self.assertFalse(is_btjd_native_time(bjd))
        self.assertTrue(np.allclose(native_time_to_bjd(bjd), bjd))
