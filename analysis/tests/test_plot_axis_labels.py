from django.test import SimpleTestCase

from analysis.auxil.plot_axis_labels import (
    FLUX_DENSITY_F_LAMBDA,
    PHASE_AXIS,
    RADIAL_VELOCITY,
    WAVELENGTH_ANGSTROM,
    format_axis_label,
    resolve_axis_labels,
)
from analysis.categories import AnalysisCategory


class PlotAxisLabelTests(SimpleTestCase):
    def test_sedfit_bare_flux_gets_cgs_unit(self):
        class _Attrs:
            def __init__(self, mapping):
                self._mapping = mapping

            def __contains__(self, key):
                return key in self._mapping

            def get(self, key):
                return self._mapping.get(key)

        class _FakeHdf:
            attrs = _Attrs({'type': 'sedfit'})
            def __contains__(self, key):
                return key == 'DATA'

            def __getitem__(self, key):
                return _Group()

        class _Group:
            attrs = _Attrs({
                'xlabel': 'Wavelength (AA)',
                'ylabel': 'flux',
                'xscale': 'log',
                'yscale': 'log',
            })

            def __iter__(self):
                return iter(())

        x_label, y_label = resolve_axis_labels(_FakeHdf(), category=AnalysisCategory.SED_FIT)
        self.assertEqual(x_label, WAVELENGTH_ANGSTROM)
        self.assertEqual(y_label, FLUX_DENSITY_F_LAMBDA)

    def test_explicit_yunit_is_used(self):
        label = format_axis_label(
            'flux',
            axis='y',
            unit='erg/s/cm2/AA',
            sed_context=True,
        )
        self.assertIn('Fλ', label)
        self.assertIn('erg', label)

    def test_non_sed_flux_stays_generic(self):
        label = format_axis_label('flux', axis='y', sed_context=False)
        self.assertEqual(label, 'Flux')

    def test_rv_curve_ignores_bogus_sed_group_attrs(self):
        class _Attrs:
            def __init__(self, mapping):
                self._mapping = mapping

            def __contains__(self, key):
                return key in self._mapping

            def get(self, key):
                return self._mapping.get(key)

        class _Series:
            attrs = _Attrs({'xpar': 'phase', 'ypar': 'rv', 'datatype': 'discrete'})

        class _Data:
            attrs = _Attrs({
                'xlabel': 'Wavelength',
                'ylabel': 'Flux density F_lambda',
                'xscale': 'log',
                'yscale': 'log',
            })

            def __iter__(self):
                return iter(('MS',))

            def __getitem__(self, key):
                return _Series()

        class _FakeHdf:
            attrs = _Attrs({'type': 'prvcurve'})

            def __contains__(self, key):
                return key == 'DATA'

            def __getitem__(self, key):
                return _Data()

        x_label, y_label = resolve_axis_labels(
            _FakeHdf(), category=AnalysisCategory.RV_CURVE,
        )
        self.assertEqual(x_label, PHASE_AXIS)
        self.assertEqual(y_label, RADIAL_VELOCITY)
