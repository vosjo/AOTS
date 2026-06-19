from __future__ import annotations

from django.db import models
from simple_history.models import HistoricalRecords

from analysis.models.default_values import COMPONENT_CHOICES, SYSTEM
from stars.models import Project

from .parameter_source import ParameterSource


class ConsensusRuleKind(models.TextChoices):
    WEIGHTED_AVERAGE = 'weighted_average', 'Weighted average'
    PREFERRED_SOURCE = 'preferred_source', 'Preferred parameter source'
    PREFERRED_ANALYSIS_CATEGORY = 'preferred_analysis_category', 'Preferred analysis category'
    SOURCE_PRIORITY = 'source_priority', 'Source priority list'
    LATEST = 'latest', 'Latest measurement'


CONSENSUS_WILDCARD = '*'


class ParameterConsensusPolicy(models.Model):
    """Project-wide rule for resolving the canonical value of a parameter."""

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='consensus_policies')
    name = models.CharField(max_length=50)
    component = models.IntegerField(choices=COMPONENT_CHOICES, default=SYSTEM)
    rule = models.CharField(max_length=40, choices=ConsensusRuleKind.choices)
    preferred_source = models.ForeignKey(
        ParameterSource,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='consensus_policies',
    )
    preferred_analysis_category = models.CharField(max_length=32, blank=True, default='')
    source_priority = models.JSONField(default=list, blank=True)
    fallback_rule = models.CharField(
        max_length=40,
        choices=ConsensusRuleKind.choices,
        blank=True,
        default='',
    )
    fallback_preferred_source = models.ForeignKey(
        ParameterSource,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='consensus_fallback_policies',
    )
    fallback_analysis_category = models.CharField(max_length=32, blank=True, default='')
    priority = models.IntegerField(default=0)

    history = HistoricalRecords(cascade_delete_history=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['project', 'name', 'component'],
                name='analysis_consensus_policy_unique',
            ),
        ]
        ordering = ['name', 'component']

    def __str__(self):
        return f'{self.project_id}:{self.name}:{self.component} ({self.rule})'
