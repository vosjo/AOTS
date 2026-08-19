from http import HTTPStatus

from django.test import TestCase

from stars.models import Project, Star
from stars.services import star_io


class IdentifierBookkeeping(TestCase):

    def setUp(self):
        p = Project.objects.create(
            name='TestCase',
            description='TestCase_description',
        )
        star_io.create_star(
            name='Vega',
            project=p,
            ra=279.23473479,
            dec=38.78368896,
        )

    def test_create_identifier_on_create_star(self):
        s = Star.objects.get(name__exact='Vega')

        i = s.identifier_set.all()

        self.assertEqual(len(i), 1,
                         "Identifier not created when star is created")
        self.assertEqual(i[0].name, s.name,
                         "Name of identifier is not equal to star name on creation")

    def test_modify_identifier_on_modify_star_name(self):
        s = Star.objects.get(name__exact='Vega')

        s.name = 'alf Lyr'
        star_io.save_star(s)

        # i = s.identifier_set.filter(name__exact='Vega')
        # self.assertEqual(len(i), 0,
        # "Old star name not removed from identifiers on star name change")

        i = s.identifier_set.filter(name__exact='alf Lyr')
        self.assertEqual(len(i), 1,
                         "New star name not added to identifiers on star name change")


#    Tests for robots.txt
#       -> adapted from https://adamj.eu/tech/2020/02/10/robots-txt/
class RobotsTxtTests(TestCase):
    def test_get(self):
        response = self.client.get("/robots.txt")

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response["content-type"], "text/plain")
        lines = response.content.decode().splitlines()
        self.assertEqual(lines[0], "User-Agent: *")


class ProjectSlugTests(TestCase):
    def test_unique_slugs_for_colliding_slugify(self):
        Project.objects.create(name='My Project')
        project_b = Project(name='My-Project')
        project_b.save()

        self.assertNotEqual(
            Project.objects.get(name='My Project').slug,
            project_b.slug,
        )
        self.assertTrue(project_b.slug)

    def test_post_disallowed(self):
        response = self.client.post("/robots.txt")

        self.assertEqual(HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
