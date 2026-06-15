from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import pre_delete, post_delete, post_save, pre_save
from django.dispatch import receiver

from analysis.services.parameter_averaging import sync_average_for
from analysis.categories import category_label
from stars.models import Star
from .analysis_model import Analysis
from .parameter_source import ParameterSource
# -- all constants are the roud_value function are imported from default values
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

    # -- provide custom sorting options that make sense
    objects = ParameterManager()

    def order(self):
        return parameter_order(self.name)

    # -- A parameter belongs to a system, and will be deleted if the system
    #   is deleted.
    star = models.ForeignKey(Star, on_delete=models.CASCADE, blank=True, null=True)

    # -- a parameter belongs to an analysis or external source, but not both.
    parameter_source = models.ForeignKey(
        ParameterSource, on_delete=models.CASCADE, blank=True, null=True,
    )
    analysis = models.ForeignKey(
        Analysis, on_delete=models.CASCADE, blank=True, null=True,
        related_name='parameter_set',
    )

    # -- name of the variable measured in this parameter
    name = models.CharField(max_length=50)

    # -- component the parameter belongs to
    component = models.IntegerField(
        choices=COMPONENT_CHOICES,
        default=SYSTEM)

    # -- add component behind name if component is primary or secondary
    cname = models.CharField(max_length=52, default='')

    value = models.FloatField(default=0.0)

    # -- errors are stored as upper and lower error, and error function is
    #   provided to return the average error in 1 value.
    #   the error field can also be directly set and will populate the
    #   error_l and _u field with the save value.
    error_l = models.FloatField(default=0.0)  # lower error
    error_u = models.FloatField(default=0.0)  # upper error

    @property
    def error(self):
        # return the error based on lower and upper error
        return (self.error_l + self.error_u) / 2.0

    @error.setter
    def error(self, val):
        # set  lower and upper error to the error value
        self.error_l = val
        self.error_u = val

    # -- unit in which this variable is measured
    unit = models.CharField(max_length=50)

    # -- valid setting to indicate wether or not this parameter is trustworthy
    valid = models.BooleanField(default=True)

    # -- set average=True to indicate this parameter contains the average
    #   of all measurements of this variable for this star. This average
    #   parameter is automatically created and updated upon saving a parameter
    average = models.BooleanField(default=False)

    def clean(self):
        if self.parameter_source_id and self.analysis_id:
            raise ValidationError('A parameter cannot belong to both an analysis and a parameter source.')

    def save(self, *args, **kwargs):
        if self.parameter_source_id and self.analysis_id:
            raise ValidationError('A parameter cannot belong to both an analysis and a parameter source.')
        super().save(*args, **kwargs)

    # -- Rounded value and errors
    def rvalue(self):
        return round_value(self.value, self.name, self.error)

    def rerror(self):
        return round_value(self.error, self.name, self.error)

    def rerror_l(self):
        return round_value(self.error_l, self.name, self.error_l)

    def rerror_u(self):
        return round_value(self.error_u, self.name, self.error_u)

    # -- representation of self
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
    """
    Subtype of an average parameter that is derived based on other parameters
    """

    source_parameters = models.ManyToManyField(Parameter, blank=True, related_name='derived_parameters')

    def create(self):
        from analysis.services import parameter_derivation as derivation_service
        return derivation_service.find_sources(self)

    def update(self):
        from analysis.services import parameter_derivation as derivation_service
        try:
            derivation_service.calculate(self)
            self.average = True
            return True
        except Exception as e:
            print(e)
            return False

    # -- representation of self
    def __str__(self):
        return "{} = {} +- {} {} -{}- ({})".format(self.cname, self.rvalue(), self.rerror(),
                                                   self.unit, 'V' if self.valid else 'F', 'DRVD')


# ======================================================================================
# cname parameter handling
# ======================================================================================

@receiver(pre_save, sender=Parameter)
@receiver(pre_save, sender=DerivedParameter)
def set_cname(sender, **kwargs):
    """
    When a parameter is created or modified, update the cname based on the
    parameter name and the component number:
    cname = name + _ + component if component is 1 or 2.
    """
    if kwargs.get('raw', False):
        return

    param = kwargs['instance']
    param.cname = combine_parameter_name(param.name, param.component)


# ======================================================================================
# AVERAGE parameter handling (delegates to analysis.services.parameter_averaging)
# ======================================================================================

@receiver(post_delete, sender=Parameter)
@receiver(post_save, sender=Parameter)
def average_parameter_bookkeeping(sender, **kwargs):
    if kwargs.get('raw', False):
        return
    sync_average_for(kwargs['instance'])


# ======================================================================================
# DERIVED parameter handling
# ======================================================================================


@receiver(pre_save, sender=DerivedParameter)
def derived_parameter_update_on_save(sender, **kwargs):
    """
    When a derived parameter is saved, update its value and error first.
    """
    if kwargs['raw']: return

    param = kwargs['instance']
    if not param._state.adding:
        # only update parameter if it is modified, not on creation
        success = param.update()

        if not success:
            param.delete()


@receiver(post_save, sender=DerivedParameter)
def derived_parameter_find_sources_on_create(sender, **kwargs):
    """
    When a new Derived parameter is created, find all necessary parameters
    to derive it from
    """
    param = kwargs['instance']

    # -- if the derived paramter is newly created, search for the needed parameters
    #   to calculate it.
    if kwargs['created']:
        param.create()
        param.save()


# @receiver(post_delete, sender=Parameter)
@receiver(post_save, sender=Parameter)
def derived_parameter_bookkeeping_on_update(sender, **kwargs):
    """
    Check if there are any derived parameters using this parameter,
    and if so, update their values
    """
    if kwargs.get('raw', False):
        return

    param = kwargs['instance']

    if param.derived_parameters.exists():
        from analysis.services import parameter_derivation as derivation_service
        derivation_service.refresh_derived_for(param)


@receiver(pre_delete, sender=Parameter)
def derived_parameter_bookkeeping_on_delete(sender, **kwargs):
    """
    Check if there are any derived parameters using this parameter,
    and if so, update their values
    """
    if kwargs.get('raw', False):
        return

    param = kwargs['instance']

    if param.derived_parameters.exists():
        from analysis.services import parameter_derivation as derivation_service
        derivation_service.delete_dependent_derived(param)
