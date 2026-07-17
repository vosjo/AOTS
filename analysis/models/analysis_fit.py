"""DB mirror of HDF5 FITS/<fit_id> groups for permissions and queries."""

from __future__ import annotations

from django.conf import settings
from django.db import models

from .analysis_model import Analysis


class AnalysisFit(models.Model):
    """One orbital/model fit inside a multi-fit Analysis container."""

    analysis = models.ForeignKey(
        Analysis,
        on_delete=models.CASCADE,
        related_name='fits',
    )
    fit_id = models.CharField(max_length=128)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='analysis_fits',
    )
    label = models.CharField(max_length=255, default='')
    method = models.CharField(max_length=255, blank=True, default='')
    is_best_fit = models.BooleanField(default=False)
    external_id = models.CharField(max_length=128, blank=True, default='')
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'analysis_analysisfit'
        constraints = [
            models.UniqueConstraint(
                fields=['analysis', 'fit_id'],
                name='analysis_fit_unique_per_container',
            ),
        ]
        ordering = ['-is_best_fit', 'label', 'fit_id']

    def __str__(self):
        return f'{self.analysis_id}:{self.fit_id}'
