from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from stars.models import Project


class InteropImportBatch(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='interop_imports')
    source = models.CharField(max_length=32, default='astra')
    filename = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=32, default='pending')
    summary = models.JSONField(default=dict, blank=True)
    warnings = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.source} import {self.pk} ({self.status})'


class InteropRecord(models.Model):
    SOURCE_ASTRA = 'astra'

    source = models.CharField(max_length=32)
    external_id = models.CharField(max_length=128)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    import_batch = models.ForeignKey(
        InteropImportBatch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='records',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['source', 'external_id', 'content_type'],
                name='interop_record_unique_external',
            ),
        ]
        indexes = [
            models.Index(fields=['source', 'external_id']),
        ]

    def __str__(self):
        return f'{self.source}:{self.external_id} -> {self.content_type_id}:{self.object_id}'
