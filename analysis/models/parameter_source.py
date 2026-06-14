from __future__ import unicode_literals

from django.db import models
from simple_history.models import HistoricalRecords

from stars.models import Project


class ParameterSource(models.Model):
    """
    External or catalog provenance for star parameters (Gaia, manual entry, etc.).
    Not used for HDF5 analysis results — those link via Parameter.analysis.
    """

    name = models.TextField(default='')
    note = models.TextField(default='')
    reference = models.TextField(default='')

    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=False)

    history = HistoricalRecords(cascade_delete_history=True)

    def get_reference_url(self):
        if self.reference != '':
            return 'http://adsabs.harvard.edu/abs/' + self.reference
        return ''

    def __str__(self):
        return "{} {}".format(self.name, '({})'.format(self.reference) if self.reference else '')


class AverageParameterSource(ParameterSource):
    """Project-scoped container for averaged and derived parameters (typically name='AVG')."""

    class Meta:
        db_table = 'analysis_averageparametersource'

    datafile = models.FileField(upload_to='datatables/', null=True)

    def save_parameters_as_csv(self):
        pass
