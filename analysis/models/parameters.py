from django.core.exceptions import ValidationError
from django.db import models

from analysis.categories import category_label
from stars.models import Star
from .analysis_model import Analysis
from .parameter_source import ParameterSource
from .default_values import *


def combine_parameter_name(name, component):
    if component in [1, 2]:
        return name + '_' + str(component)
    else:
        return name


class ParameterManager(models.Manager):
    """
    Custom manager for Parameter class to provide sorting of the parameters in a more
    sensible fashion than alphabetical (provides standard order options)
    """

    def order(self, *args, **kwargs):
        parameters = list(self.get_queryset())
        return sorted(parameters, key=lambda t: t.order())


class Parameter(models.Model):
    """
    A simple parameter belonging to a parameter set
    The parameter consists of a value, error and unit
    """

    objects = ParameterManager()

    def order(self):
        return parameter_order(self.name)

    star = models.ForeignKey(Star, on_delete=models.CASCADE, blank=True, null=True)

    parameter_source = models.ForeignKey(
        ParameterSource, on_delete=models.CASCADE, blank=True, null=True,
    )
    analysis = models.ForeignKey(
        Analysis, on_delete=models.CASCADE, blank=True, null=True,
        related_name='parameter_set',
    )

    name = models.CharField(max_length=50)

    component = models.IntegerField(
        choices=COMPONENT_CHOICES,
        default=SYSTEM)

    cname = models.CharField(max_length=52, default='')

    value = models.FloatField(default=0.0)

    error_l = models.FloatField(default=0.0)
    error_u = models.FloatField(default=0.0)

    @property
    def error(self):
        return (self.error_l + self.error_u) / 2.0

    @error.setter
    def error(self, val):
        self.error_l = val
        self.error_u = val

    unit = models.CharField(max_length=50)

    valid = models.BooleanField(default=True)

    # Materialized consensus cache metadata (average=True rows only).
    # The ``average`` flag marks the cached consensus row, not a semantic average.
    consensus_rule = models.CharField(max_length=40, blank=True, default='')
    consensus_provenance = models.CharField(max_length=200, blank=True, default='')
    consensus_from = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='consensus_caches',
    )

    average = models.BooleanField(default=False)

    def clean(self):
        if self.parameter_source_id and self.analysis_id:
            raise ValidationError('A parameter cannot belong to both an analysis and a parameter source.')

    def save(self, *args, **kwargs):
        if self.parameter_source_id and self.analysis_id:
            raise ValidationError('A parameter cannot belong to both an analysis and a parameter source.')
        if self.star_id:
            from AOTS.project_scoping import require_same_project
            if self.analysis_id:
                require_same_project(self.star.project, self.analysis, 'Analysis')
                if self.analysis.star_id and self.star_id != self.analysis.star_id:
                    raise ValidationError('Parameter star must match the linked analysis star.')
            if self.parameter_source_id:
                require_same_project(self.star.project, self.parameter_source, 'Parameter source')
        self.cname = combine_parameter_name(self.name, self.component)
        super().save(*args, **kwargs)

    def rvalue(self):
        return round_value(self.value, self.name, self.error)

    def rerror(self):
        return round_value(self.error, self.name, self.error)

    def rerror_l(self):
        return round_value(self.error_l, self.name, self.error_l)

    def rerror_u(self):
        return round_value(self.error_u, self.name, self.error_u)

    def __str__(self):
        if self.analysis_id:
            try:
                ds = category_label(self.analysis.category)[0:10]
            except Analysis.DoesNotExist:
                ds = ''
        elif self.parameter_source_id:
            try:
                ds = self.parameter_source.name[0:10]
            except ParameterSource.DoesNotExist:
                ds = ''
        else:
            ds = ''
        return "{} = {} +- {} {} -{}- ({})".format(self.cname, self.rvalue(), self.rerror(),
                                                   self.unit, 'V' if self.valid else 'F', ds)


class DerivedParameter(Parameter):
    """Subtype of an average parameter that is derived based on other parameters."""

    source_parameters = models.ManyToManyField(Parameter, blank=True, related_name='derived_parameters')

    def __str__(self):
        return "{} = {} +- {} {} -{}- ({})".format(self.cname, self.rvalue(), self.rerror(),
                                                   self.unit, 'V' if self.valid else 'F', 'DRVD')
