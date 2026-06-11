from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from analysis.categories import (
    DatasetCategory,
    resolve_category,
    category_label,
    category_color,
)
from analysis.models import DataSet
from stars.models import Project, Star


class CategoryRegistryTests(TestCase):
    def test_resolve_known_aliases(self):
        self.assertEqual(resolve_category('RV')[0], DatasetCategory.RV_SOLUTION)
        self.assertEqual(resolve_category('RC')[0], DatasetCategory.RV_CURVE)
        self.assertEqual(resolve_category('sedfit')[0], DatasetCategory.SED_FIT)
        self.assertEqual(resolve_category('GF')[0], DatasetCategory.GENERIC)

    def test_resolve_unknown(self):
        category, source = resolve_category('custom_slug')
        self.assertEqual(category, DatasetCategory.UNKNOWN)
        self.assertEqual(source, 'auto')

    def test_category_label_and_color(self):
        self.assertEqual(category_label(DatasetCategory.RV_SOLUTION), 'RV solution')
        self.assertTrue(category_color(DatasetCategory.RV_SOLUTION).startswith('#'))


class DataSetCategoryModelTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='CatProject', slug='cat-project', is_public=True)
        self.star = Star.objects.create(name='CatStar', project=self.project, ra=1.0, dec=2.0)

    def test_multiple_datasets_same_category(self):
        for index in range(2):
            upload = SimpleUploadedFile(f'test-{index}.h5', b'hdf5')
            DataSet.objects.create(
                name=f'Dataset {index}',
                project=self.project,
                star=self.star,
                category=DatasetCategory.RV_SOLUTION,
                datafile=upload,
            )
        self.assertEqual(
            DataSet.objects.filter(star=self.star, category=DatasetCategory.RV_SOLUTION).count(),
            2,
        )
