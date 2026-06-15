from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from analysis.models import Analysis, Parameter
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
        mock_info.return_value = ('Vega', 279.23, 38.78, 'rv', 'note', '', 'RV')
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
