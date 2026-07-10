from django.test import SimpleTestCase
import numpy as np

from interop.rv_time import (
    SCALE_BJD,
    SCALE_MJD,
    astra_time_json_from_epoch,
    bjd_to_mjd,
    guess_time_scale,
    mjd_to_bjd,
)


class RvTimeTests(SimpleTestCase):
    def test_guess_bjd_from_magnitude(self):
        self.assertEqual(guess_time_scale(np.array([2458000.0, 2458010.0])), SCALE_BJD)

    def test_guess_mjd_from_magnitude(self):
        self.assertEqual(guess_time_scale(np.array([58000.0, 58010.0])), SCALE_MJD)

    def test_guess_from_xpar(self):
        self.assertEqual(guess_time_scale(np.array([58000.0]), xpar='MJD'), SCALE_MJD)
        self.assertEqual(guess_time_scale(np.array([58000.0]), xpar='BJD'), SCALE_BJD)

    def test_astra_time_json_mjd_native(self):
        t = astra_time_json_from_epoch(58000.0, scale=SCALE_MJD)
        self.assertEqual(t['scale'], SCALE_MJD)
        self.assertAlmostEqual(t['val'], 58000.0)
        self.assertAlmostEqual(t['mjd'], 58000.0)
        self.assertAlmostEqual(t['bjd'], mjd_to_bjd(58000.0))

    def test_astra_time_json_bjd_native(self):
        t = astra_time_json_from_epoch(2458000.0, scale=SCALE_BJD)
        self.assertAlmostEqual(t['bjd'], 2458000.0)
        self.assertAlmostEqual(t['mjd'], bjd_to_mjd(2458000.0))
