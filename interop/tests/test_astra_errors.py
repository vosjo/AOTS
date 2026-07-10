from django.test import SimpleTestCase

from interop.astra_errors import (
    apply_astra_errors,
    err_bounds_from_astra,
    errors_from_aots_raw,
    nearly_symmetric,
    read_astra_param_errors,
)


class AstraErrorsTests(SimpleTestCase):
    def test_nearly_symmetric(self):
        self.assertTrue(nearly_symmetric(5.0, 5.0))
        self.assertTrue(nearly_symmetric(5.0, 5.4))
        self.assertFalse(nearly_symmetric(3.0, 8.0))

    def test_errors_from_aots_raw_dict(self):
        value, err_l, err_u = errors_from_aots_raw({
            'value': 42.0,
            'err_l': 2.0,
            'err_u': 4.0,
        })
        self.assertAlmostEqual(value, 42.0)
        self.assertAlmostEqual(err_l, 2.0)
        self.assertAlmostEqual(err_u, 4.0)

    def test_apply_astra_errors_asymmetric(self):
        out: dict = {}
        apply_astra_errors(out, err_key='KErr', err_l=3.0, err_u=8.0)
        self.assertAlmostEqual(out['KErr'], 5.5)
        self.assertAlmostEqual(out['KErrUp'], 8.0)
        self.assertAlmostEqual(out['KErrDown'], 3.0)

    def test_apply_astra_errors_symmetric_only(self):
        out: dict = {}
        apply_astra_errors(out, err_key='periodErr', err_l=0.1, err_u=0.1)
        self.assertAlmostEqual(out['periodErr'], 0.1)
        self.assertNotIn('periodErrUp', out)
        self.assertNotIn('periodErrDown', out)

    def test_read_astra_param_errors(self):
        fit = {'KErr': 5.0, 'KErrUp': 8.0, 'KErrDown': 3.0}
        sym, err_l, err_u = read_astra_param_errors(fit, 'KErr')
        self.assertAlmostEqual(sym, 5.0)
        self.assertAlmostEqual(err_l, 3.0)
        self.assertAlmostEqual(err_u, 8.0)

    def test_err_bounds_from_astra_symmetric_fallback(self):
        err_l, err_u = err_bounds_from_astra(0.5, None, None)
        self.assertAlmostEqual(err_l, 0.5)
        self.assertAlmostEqual(err_u, 0.5)
