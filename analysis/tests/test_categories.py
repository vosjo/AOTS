from django.test import TestCase

from analysis.categories import (
    AnalysisCategory,
    category_color,
    category_for_hdf5,
    category_label,
    resolve_category,
    uses_sed_hdf5_reader,
)
from analysis.models import Analysis
from stars.models import Project, Star


class CategoryResolutionTests(TestCase):
    def test_resolve_category(self):
        self.assertEqual(resolve_category('RV')[0], AnalysisCategory.RV_SOLUTION)
        self.assertEqual(resolve_category('RC')[0], AnalysisCategory.RV_CURVE)
        self.assertEqual(resolve_category('sedfit')[0], AnalysisCategory.SED_FIT)
        self.assertEqual(resolve_category('GF')[0], AnalysisCategory.GENERIC)

    def test_unknown_category(self):
        category, _source = resolve_category('not-a-real-type')
        self.assertEqual(category, AnalysisCategory.UNKNOWN)

    def test_category_label_and_color(self):
        self.assertEqual(category_label(AnalysisCategory.RV_SOLUTION), 'RV solution')
        self.assertTrue(category_color(AnalysisCategory.RV_SOLUTION).startswith('#'))

    def test_category_for_hdf5_sed_layout(self):
        sed_data = {
            'results': {'iminimize': {'CI': {}}},
            'info': {'oname': 'star', 'jradeg': 0.0, 'jdedeg': 0.0},
        }
        self.assertEqual(category_for_hdf5(sed_data), AnalysisCategory.SED_FIT)
        self.assertTrue(uses_sed_hdf5_reader(sed_data))

    def test_category_for_hdf5_generic_type(self):
        generic_data = {'type': 'RV', 'systemname': 'star', 'ra': 0.0, 'dec': 0.0}
        self.assertEqual(category_for_hdf5(generic_data), AnalysisCategory.RV_SOLUTION)
        self.assertFalse(uses_sed_hdf5_reader(generic_data))


class AnalysisCategoryModelTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='Test', description='Test')
        self.star = Star.objects.create(
            name='Vega', project=self.project, ra=279.23, dec=38.78,
        )

    def test_analysis_category_persisted(self):
        Analysis.objects.create(
            name='rv1',
            project=self.project,
            star=self.star,
            category=AnalysisCategory.RV_SOLUTION,
        )
        self.assertEqual(
            Analysis.objects.filter(star=self.star, category=AnalysisCategory.RV_SOLUTION).count(),
            1,
        )
