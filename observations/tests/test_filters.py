from django.contrib.auth import get_user_model
from django.test import TestCase

from observations.api.filter import LightCurveFilter, UserInfoFilter
from observations.models import LightCurve, Spectrum, UserInfo
from stars.models import Project, Star

User = get_user_model()


class ObservationFilterTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            name='FilterProject',
            slug='filter-project',
            is_public=True,
        )
        self.star = Star.objects.create(
            name='FilterStar',
            project=self.project,
            ra=0.0,
            dec=0.0,
        )
        self.spectrum = Spectrum.objects.create(
            project=self.project,
            star=self.star,
            hjd=58000.0,
        )
        self.userinfo = UserInfo.objects.create(
            project=self.project,
            spectrum=self.spectrum,
            hjd=58000.0,
        )
        self.lightcurve = LightCurve.objects.create(
            project=self.project,
            star=self.star,
            hjd=58000.0,
        )

    def test_userinfo_star_name_filter(self):
        filt = UserInfoFilter({'target': 'Filter'}, queryset=UserInfo.objects.all())
        self.assertTrue(filt.qs.filter(pk=self.userinfo.pk).exists())

    def test_lightcurve_star_name_filter(self):
        filt = LightCurveFilter({'target': 'Filter'}, queryset=LightCurve.objects.all())
        self.assertTrue(filt.qs.filter(pk=self.lightcurve.pk).exists())
