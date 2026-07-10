from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from simple_history.models import HistoricalRecords

from analysis.categories import AnalysisCategory, CategorySource, category_label
from stars.models import Star, Project


class Analysis(models.Model):
    """HDF5 analysis result (RV, SED fit, etc.) — standalone, not a parameter source."""

    id = models.AutoField(primary_key=True)

    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=False)
    name = models.TextField(default='')
    note = models.TextField(default='')
    reference = models.TextField(default='')

    star = models.ForeignKey(Star, on_delete=models.CASCADE, blank=True, null=True)

    spectrum = models.ForeignKey(
        'observations.Spectrum',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='analyses',
    )
    lightcurve = models.ForeignKey(
        'observations.LightCurve',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='analyses',
    )

    category = models.CharField(
        max_length=32,
        choices=AnalysisCategory.choices,
        default=AnalysisCategory.UNKNOWN,
    )
    category_source = models.CharField(
        max_length=8,
        choices=CategorySource.choices,
        default=CategorySource.AUTO,
    )
    file_type = models.CharField(max_length=32, default='', blank=True)

    datafile = models.FileField(upload_to='analyses/')
    fit = models.BooleanField(default=True)
    is_best_fit = models.BooleanField(default=False)

    history = HistoricalRecords(cascade_delete_history=True)

    class Meta:
        db_table = 'analysis_analysis'
        verbose_name_plural = 'analyses'
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(spectrum__isnull=False, lightcurve__isnull=False),
                name='analysis_single_observation_parent',
            ),
        ]

    def get_category_display(self):
        return category_label(self.category)

    def get_reference_url(self):
        if self.reference != '':
            return 'http://adsabs.harvard.edu/abs/' + self.reference
        return ''

    def clean(self):
        if self.spectrum_id and self.lightcurve_id:
            raise ValidationError('Analysis cannot reference both a spectrum and a light curve.')

    def save(self, *args, **kwargs):
        if self.spectrum_id:
            from AOTS.project_scoping import require_same_project
            require_same_project(self.project, self.spectrum, 'Spectrum')
        if self.lightcurve_id:
            from AOTS.project_scoping import require_same_project
            require_same_project(self.project, self.lightcurve, 'LightCurve')
        if self.star_id:
            from AOTS.project_scoping import require_same_project
            require_same_project(self.project, self.star, 'Star')
        super().save(*args, **kwargs)

    def __str__(self):
        return "{} {}".format(self.name, '({})'.format(self.reference) if self.reference else '')

    def get_data(self):
        from analysis.services.analysis_io import read_analysis_data
        return read_analysis_data(self)


@receiver(post_delete, sender=Analysis)
def analysis_post_delete_handler(sender, **kwargs):
    analysis = kwargs['instance']
    same_datafile = Analysis.objects.filter(datafile=analysis.datafile)
    if not same_datafile.exists():
        storage, path = analysis.datafile.storage, analysis.datafile.path
        storage.delete(path)
