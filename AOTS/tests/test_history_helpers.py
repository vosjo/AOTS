from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from AOTS.history_helpers import find_history_user, history_actor_for_changelog
from analysis.models import Analysis
from stars.models import Project, Star


class HistoryActorTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='alice',
            password='test',
        )
        self.project = Project.objects.create(name='P', slug='p')
        self.star = Star.objects.create(
            name='HD 1',
            project=self.project,
            ra=10.0,
            dec=20.0,
        )

    def test_find_history_user_falls_back_to_creator(self):
        analysis = Analysis(
            project=self.project,
            star=self.star,
            name='RV curve',
            datafile=SimpleUploadedFile('rv.h5', b'x'),
        )
        analysis._history_user = self.user
        analysis.save()
        analysis = Analysis.objects.get(pk=analysis.pk)
        analysis.name = 'RV curve updated'
        analysis.save()

        self.assertIsNone(analysis.history.latest().history_user)
        self.assertEqual(find_history_user(analysis), self.user)
        actor, label = history_actor_for_changelog(analysis)
        self.assertEqual(actor, self.user)
        self.assertEqual(label, 'alice')

    def test_history_actor_without_any_user(self):
        analysis = Analysis.objects.create(
            project=self.project,
            star=self.star,
            name='Orphan',
            datafile=SimpleUploadedFile('orphan.h5', b'x'),
        )
        actor, label = history_actor_for_changelog(analysis)
        self.assertIsNone(actor)
        self.assertEqual(label, 'system')
