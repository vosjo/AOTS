from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from analysis.categories import AnalysisCategory, category_derived_parameters
from analysis.models import Analysis, DerivedParameter, Parameter
from analysis.services.analysis_ingestion import ingest_analysis_file
from stars.models import Project, Star


class IngestionTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='Ingest', description='')
        self.star = Star.objects.create(
            name='Vega', project=self.project, ra=279.23, dec=38.78,
        )

    @patch('analysis.services.analysis_ingestion.read_analyses.get_basic_info')
    @patch('analysis.models.analysis_model.Analysis.get_data')
    @patch('analysis.auxil.read_analyses.get_parameters')
    def test_ingest_sets_analysis_on_parameters(self, mock_params, mock_data, mock_info):
        mock_data.return_value = {}
        mock_info.return_value = ('Vega', 279.23, 38.78, 'rv', 'note', '', 'SF')
        mock_params.return_value = {'teff': (5000.0, 100.0, 100.0, 'K')}

        analysis = Analysis.objects.create(
            project=self.project,
            datafile=SimpleUploadedFile('t.h5', b'x'),
        )
        result = ingest_analysis_file(analysis.pk)
        self.assertTrue(result.success)
        param = Parameter.objects.get(analysis=analysis)
        self.assertEqual(param.analysis_id, analysis.pk)
        self.assertIsNone(param.parameter_source_id)

    @patch('analysis.services.analysis_ingestion.read_analyses.get_basic_info')
    @patch('analysis.models.analysis_model.Analysis.get_data')
    @patch('analysis.auxil.read_analyses.get_parameters')
    def test_rv_ingest_creates_derived_parameters(self, mock_params, mock_data, mock_info):
        mock_data.return_value = {}
        mock_info.return_value = ('Vega', 279.23, 38.78, 'rv fit', 'note', '', 'RV')
        mock_params.return_value = {
            'K1': (5.0, 0.5, 0.5, 'km/s'),
            'K2': (10.0, 1.0, 1.0, 'km/s'),
            'p': (10.0, 0.1, 0.1, 'd'),
            'e': (0.0, 0.01, 0.01, ''),
        }

        analysis = Analysis.objects.create(
            project=self.project,
            datafile=SimpleUploadedFile('rv.h5', b'x'),
        )
        result = ingest_analysis_file(analysis.pk)
        self.assertTrue(result.success)
        analysis.refresh_from_db()
        self.assertEqual(analysis.category, AnalysisCategory.RV_CURVE)
        self.assertIn('derived parameters', result.message)

        derived = DerivedParameter.objects.filter(star=self.star).order_by('name', 'component')
        self.assertEqual(derived.count(), 5)
        names = {(d.name, d.component) for d in derived}
        self.assertEqual(names, {
            ('q', 0), ('msini', 1), ('msini', 2), ('asini', 1), ('asini', 2),
        })

        q = derived.get(name='q', component=0)
        self.assertAlmostEqual(q.value, 0.5, places=1)
        self.assertTrue(q.average)
        self.assertGreater(q.source_parameters.count(), 0)

    def test_rv_category_defines_derived_parameters(self):
        params = category_derived_parameters(AnalysisCategory.RV_CURVE)
        self.assertEqual(params, 'q,msini1,msini2,asini1,asini2')

    @patch('analysis.services.analysis_ingestion.read_analyses.get_basic_info')
    @patch('analysis.models.analysis_model.Analysis.get_data')
    @patch('analysis.auxil.read_analyses.get_parameters')
    def test_category_override_creates_derived_when_file_type_unknown(
        self, mock_params, mock_data, mock_info,
    ):
        mock_data.return_value = {}
        mock_info.return_value = ('Vega', 279.23, 38.78, 'rv fit', 'note', '', '??')
        mock_params.return_value = {
            'K1': (5.0, 0.5, 0.5, 'km/s'),
            'K2': (10.0, 1.0, 1.0, 'km/s'),
            'p': (10.0, 0.1, 0.1, 'd'),
            'e': (0.0, 0.01, 0.01, ''),
        }

        analysis = Analysis.objects.create(
            project=self.project,
            datafile=SimpleUploadedFile('rv.h5', b'x'),
        )
        result = ingest_analysis_file(
            analysis.pk,
            category_override=AnalysisCategory.RV_CURVE,
        )
        self.assertTrue(result.success)
        analysis.refresh_from_db()
        self.assertEqual(analysis.category, AnalysisCategory.RV_CURVE)
        self.assertEqual(analysis.category_source, 'user')
        self.assertIn('derived parameters', result.message)
        self.assertEqual(DerivedParameter.objects.filter(star=self.star).count(), 5)
