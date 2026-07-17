"""Maps legacy analysis PKs to multi-fit container + fit_id after migration."""

from django.db import models

from .analysis_model import Analysis


class AnalysisRedirect(models.Model):
    old_analysis_id = models.IntegerField(unique=True)
    container = models.ForeignKey(
        Analysis,
        on_delete=models.CASCADE,
        related_name='legacy_redirects',
    )
    fit_id = models.CharField(max_length=128, blank=True, default='')

    class Meta:
        db_table = 'analysis_analysisredirect'

    def __str__(self):
        return f'{self.old_analysis_id} -> {self.container_id}?fit_id={self.fit_id}'
