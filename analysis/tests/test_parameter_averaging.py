import numpy as np
from django.test import SimpleTestCase

from analysis.services.parameter_averaging import calculate_average


class _ParamStub:
    def __init__(self, value, error_l, error_u):
        self.value = value
        self.error_l = error_l
        self.error_u = error_u


class _QueryStub:
    def __init__(self, rows):
        self._rows = rows

    def values_list(self, field, flat=False):
        if field == 'value':
            return [r.value for r in self._rows]
        if field == 'error_l':
            return [r.error_l for r in self._rows]
        if field == 'error_u':
            return [r.error_u for r in self._rows]
        raise KeyError(field)


class CalculateAverageTests(SimpleTestCase):
    def test_inverse_variance_two_measurements(self):
        params = _QueryStub([
            _ParamStub(30000, 5000, 5000),
            _ParamStub(35000, 3000, 3000),
        ])
        value, error = calculate_average(params)
        self.assertAlmostEqual(value, 33676.471, places=3)
        self.assertAlmostEqual(error, 2572.479, places=3)

    def test_inverse_variance_equal_uncertainties(self):
        params = _QueryStub([
            _ParamStub(10.0, 1.0, 1.0),
            _ParamStub(12.0, 1.0, 1.0),
        ])
        value, error = calculate_average(params)
        self.assertAlmostEqual(value, 11.0)
        self.assertAlmostEqual(error, 1.0 / np.sqrt(2.0))

    def test_asymmetric_errors_use_midpoint_sigma(self):
        params = _QueryStub([
            _ParamStub(1.0, 0.2, 0.8),
        ])
        value, error = calculate_average(params)
        self.assertAlmostEqual(value, 1.0)
        self.assertAlmostEqual(error, 0.5)
