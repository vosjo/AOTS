from django.test import TestCase

from stars.models import Identifier, Project
from stars.services import star_io


class StarIoTests(TestCase):

    def setUp(self):
        self.project = Project.objects.create(
            name='TestCase',
            description='TestCase_description',
        )

    def test_create_star_adds_primary_identifier(self):
        star = star_io.create_star(
            name='Vega',
            project=self.project,
            ra=279.23473479,
            dec=38.78368896,
        )
        identifiers = star.identifier_set.all()
        self.assertEqual(len(identifiers), 1)
        self.assertEqual(identifiers[0].name, star.name)

    def test_save_star_after_rename_adds_new_identifier(self):
        star = star_io.create_star(
            name='Vega',
            project=self.project,
            ra=279.23473479,
            dec=38.78368896,
        )
        star.name = 'alf Lyr'
        star_io.save_star(star)

        self.assertEqual(star.identifier_set.filter(name='Vega').count(), 1)
        self.assertEqual(star.identifier_set.filter(name='alf Lyr').count(), 1)

    def test_identifier_save_sets_project_from_star(self):
        star = star_io.create_star(
            name='Vega',
            project=self.project,
            ra=0.0,
            dec=0.0,
        )
        ident = Identifier.objects.get(name='Vega', star=star)
        self.assertEqual(ident.project_id, self.project.pk)
