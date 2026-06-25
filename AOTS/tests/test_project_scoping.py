from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from analysis.models import Analysis, Parameter, ParameterSource
from observations.models import LightCurve, Observatory, RawSpecFile, Spectrum
from observations.plotting import plot_sed
from stars.api.filter import StarFilter
from stars.api.serializers import StarSerializer, TagSerializer
from stars.models import Project, Star, Tag

User = get_user_model()


class ModelProjectScopingTests(TestCase):
    def setUp(self):
        self.project_a = Project.objects.create(name='A', description='', is_public=True)
        self.project_b = Project.objects.create(name='B', description='', is_public=True)
        self.star_a = Star.objects.create(name='SA', project=self.project_a, ra=0, dec=0)
        self.star_b = Star.objects.create(name='SB', project=self.project_b, ra=1, dec=1)
        self.obs_b = Observatory.objects.create(project=self.project_b, name='ObsB')

    def test_analysis_rejects_star_from_other_project(self):
        analysis = Analysis(project=self.project_a, name='rv', star=self.star_b)
        with self.assertRaises(ValidationError):
            analysis.save()

    def test_spectrum_rejects_star_from_other_project(self):
        spectrum = Spectrum(project=self.project_a, star=self.star_b, hjd=1.0)
        with self.assertRaises(ValidationError):
            spectrum.save()

    def test_spectrum_rejects_observatory_from_other_project(self):
        spectrum = Spectrum(project=self.project_a, star=self.star_a, observatory=self.obs_b, hjd=1.0)
        with self.assertRaises(ValidationError):
            spectrum.save()

    def test_lightcurve_rejects_star_from_other_project(self):
        lc = LightCurve(project=self.project_a, star=self.star_b, hjd=1.0)
        with self.assertRaises(ValidationError):
            lc.save()

    def test_parameter_rejects_analysis_from_other_project(self):
        analysis_b = Analysis.objects.create(
            project=self.project_b, star=self.star_b, name='sed',
        )
        param = Parameter(
            star=self.star_a,
            analysis=analysis_b,
            name='teff',
            component=0,
            value=5000,
            unit='K',
        )
        with self.assertRaises(ValidationError):
            param.save()

    def test_parameter_rejects_source_from_other_project(self):
        source_b = ParameterSource.objects.create(name='Gaia', project=self.project_b)
        param = Parameter(
            star=self.star_a,
            parameter_source=source_b,
            name='teff',
            component=0,
            value=5000,
            unit='K',
        )
        with self.assertRaises(ValidationError):
            param.save()

    def test_rawspecfile_rejects_foreign_project_star(self):
        raw = RawSpecFile.objects.create(
            project=self.project_a,
            rawfile=SimpleUploadedFile('raw.fits', b'x'),
        )
        with self.assertRaises(ValidationError):
            raw.star.add(self.star_b)


class PlotProjectScopingTests(TestCase):
    def setUp(self):
        self.project_a = Project.objects.create(name='A', description='', is_public=True)
        self.project_b = Project.objects.create(name='B', description='', is_public=True)
        self.star_a = Star.objects.create(name='SA', project=self.project_a, ra=0, dec=0)

    def test_plot_sed_rejects_foreign_project(self):
        with self.assertRaises(ValidationError):
            plot_sed(self.star_a.pk, project=self.project_b)


class StarFilterProjectScopingTests(TestCase):
    def setUp(self):
        self.project_a = Project.objects.create(name='A', description='', is_public=True)
        self.project_b = Project.objects.create(name='B', description='', is_public=True)
        self.star_a = Star.objects.create(name='SA', project=self.project_a, ra=0, dec=0)
        self.tag_a = Tag.objects.create(name='tag-a', project=self.project_a, color='#fff')
        self.tag_b = Tag.objects.create(name='tag-b', project=self.project_b, color='#000')
        self.star_a.tags.add(self.tag_a)

    def test_tag_filter_ignores_foreign_project_tags(self):
        filt = StarFilter(
            data={'project': self.project_a.pk, 'tags': str(self.tag_b.pk)},
            queryset=Star.objects.all(),
        )
        self.assertTrue(filt.is_valid(), filt.errors)
        self.assertEqual(list(filt.qs), [])


class StarSerializerProjectScopingTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(username='rw', password='x')
        self.project_a = Project.objects.create(name='A', description='', is_public=False)
        self.project_b = Project.objects.create(name='B', description='', is_public=False)
        self.project_a.readwrite_users.add(self.user)
        self.star = Star.objects.create(name='S', project=self.project_a, ra=0, dec=0)
        self.tag_a = Tag.objects.create(name='tag-a', project=self.project_a, color='#fff')
        self.tag_b = Tag.objects.create(name='tag-b', project=self.project_b, color='#000')

    def test_star_patch_rejects_foreign_project_tags(self):
        request = self.factory.patch('/')
        force_authenticate(request, user=self.user)
        serializer = StarSerializer(
            self.star,
            data={'tag_ids': [self.tag_b.pk]},
            partial=True,
            context={'request': request},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('tag_ids', serializer.errors)

    def test_star_patch_accepts_same_project_tags(self):
        request = self.factory.patch('/')
        force_authenticate(request, user=self.user)
        serializer = StarSerializer(
            self.star,
            data={'tag_ids': [self.tag_a.pk]},
            partial=True,
            context={'request': request},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_star_patch_cannot_move_to_other_project(self):
        request = self.factory.patch('/')
        force_authenticate(request, user=self.user)
        serializer = StarSerializer(
            self.star,
            data={'project': self.project_b.pk},
            partial=True,
            context={'request': request},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        self.star.refresh_from_db()
        self.assertEqual(self.star.project_id, self.project_a.pk)

    def test_star_create_rejects_foreign_project_without_add_permission(self):
        request = self.factory.post('/')
        force_authenticate(request, user=self.user)
        serializer = StarSerializer(
            data={
                'name': 'New',
                'project': self.project_b.pk,
                'ra': 0,
                'dec': 0,
                'tag_ids': [],
            },
            context={'request': request},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('project', serializer.errors)

    def test_tag_patch_cannot_move_to_other_project(self):
        tag = Tag.objects.create(name='t', project=self.project_a, color='#fff')
        request = self.factory.patch('/')
        force_authenticate(request, user=self.user)
        serializer = TagSerializer(
            tag,
            data={'project': self.project_b.pk},
            partial=True,
            context={'request': request},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        tag.refresh_from_db()
        self.assertEqual(tag.project_id, self.project_a.pk)
