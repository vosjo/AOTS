from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from analysis.auxil.process_analyses import create_parameters
from analysis.models import Analysis, Parameter
from stars.models import Project, Star


class CreateParametersProvenanceTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='Test', description='Test')
        self.star = Star.objects.create(
            name='Vega', project=self.project, ra=279.23, dec=38.78,
        )
        self.analysis = Analysis.objects.create(
            name='rv fit',
            project=self.project,
            star=self.star,
            datafile=SimpleUploadedFile('test.h5', b'hdf5'),
        )

    @patch('analysis.auxil.read_analyses.get_parameters')
    def test_create_parameters_sets_analysis_not_parameter_source(self, mock_get_parameters):
        mock_get_parameters.return_value = {
            'teff': (12000.0, 500.0, 500.0, 'K'),
        }
        create_parameters(self.analysis, object())

        param = Parameter.objects.get(analysis=self.analysis, name='teff')
        self.assertEqual(param.analysis_id, self.analysis.pk)
        self.assertIsNone(param.parameter_source_id)
