from __future__ import unicode_literals

from django.conf import settings
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver

from analysis.auxil import fileio
from analysis.auxil import plot_datasets
from stars.models import Star, Project
from users.models import get_sentinel_user
# -- all constants are the roud_value function are imported from default values
from .default_values import *


class Method(models.Model):
    """
    This class represents different types of analysis methods, so that new ones
    can be added without the need to change the source code.
    """

    name = models.TextField(default='')
    description = models.TextField(default='')

    # -- a method belongs to a specific project in the same way as a tag does. If the project is
    #   deleted, the method should go to.
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=False, )

    # -- short name for the method without spaces. To be used in determining
    #   the method used in uploaded files
    # slug = models.SlugField(max_length=10, default='', unique=True)
    slug = models.SlugField(max_length=10, default='')

    #   Color as hex color value
    color = models.CharField(max_length=7, default='#8B0000')

    # -- plot type defines what the structure of the hdf5 file is
    data_type = models.CharField(max_length=7, choices=PLOT_CHOISES, default=GENERIC)

    # --automatically derived parameters stored as ',' separated string
    derived_parameters = models.TextField(default='')

    # -- bookkeeping
    added_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET(get_sentinel_user),
        null=True,
        )

    # -- representation of self
    def __str__(self):
        return "{} - {}".format(self.name, self.description)

    # -- set the slug on save if it is empty
    def save(self, **kwargs):
        if self.slug == '':
            self.slug = self.name.replace(" ", "")
        super(Method, self).save(**kwargs)


class DataSource(models.Model):
    """
    Super class for any object that has parameters attached.
    """

    name = models.TextField(default='')
    note = models.TextField(default='')
    reference = models.TextField(default='')

    # -- A datasource belongs to a specific project. If the project is
    #   deleted, the method should go to.
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=False)

    # -- bookkeeping
    added_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET(get_sentinel_user),
        null=True,
        )
    modified_by = models.TextField(default='')

    def source(self):
        """
        Returns a string representation of the source of the parameters
        depending on whether this object is a DataSet, DataTable or
        a random source
        """
        try:
            return self.dataset.method.name
        except DataSet.DoesNotExist:
            return self.reference if self.reference != '' else self.name

    def get_reference_url(self):
        if self.reference != '':
            return 'http://adsabs.harvard.edu/abs/' + self.reference
        else:
            return ''

    # -- representation of self
    def __str__(self):
        return "{} {}".format(self.name, '({})'.format(self.reference) if self.reference else '')


class AverageDataSource(DataSource):
    """
    Data source class to contain the average parameters of this project. Can only be one per project
    """

    # def __init__(self, *args, **kwargs):
    # kwargs['name'] = 'AVG'
    # super(AverageDataSource, self).__init__(*args, **kwargs)

    # -- the table with all average parameters is stored in as a csv file
    datafile = models.FileField(upload_to='datatables/', null=True)

    def save_parameters_as_csv(self):
        """
        Method to save all average parameters to a text file in CSV format.
        """
        pass


class DataTable(DataSource):
    # -- the table is stored in a txt file
    datafile = models.FileField(upload_to='datatables/', null=True)

    # -- ';' separated list of the column names, each name should correspond
    #   with a recognizable parameter name.
    columnnames = models.TextField(default='')

    # -- table dimensions
    xdim = models.IntegerField(default=0)
    ydim = models.IntegerField(default=0)


class DataSet(DataSource):
    # -- the dataset belongs to one star, and is deleted when the star is
    #   removed.
    star = models.ForeignKey(Star, on_delete=models.CASCADE, blank=True, null=True)

    # -- analysis method used for this dataset
    method = models.ForeignKey(Method, on_delete=models.CASCADE, blank=True, null=True)

    # -- the actual results are stored in a hdf5 file
    datafile = models.FileField(upload_to='datasets/')

    # -- valid setting to indicate wether or not this dataset is trustworthy
    valid = models.BooleanField(default=True)

    def get_data(self):
        return fileio.read2dict(self.datafile.path)

    def make_figure(self):
        """
        Method for returning the bokeh figure showing the results
        of this dataset.
        """
        return plot_datasets.plot_dataset(self.datafile.path, self.method)

    def make_large_figure(self):
        """
        Method for returning a large bokeh figure showing the results
        of this dataset.
        """
        return plot_datasets.plot_dataset_large(self.datafile.path, self.method)

    def make_OC_figure(self):
        """
        Method for returning a bokeh figure showing the O-C
        of this dataset.
        """
        return plot_datasets.plot_dataset_oc(self.datafile.path, self.method)

    def make_parameter_hist_figures(self):
        """
        Returns a figure for each parameters that plots the distribution as a histogram
        """
        return plot_datasets.plot_generic_hist(self.datafile.path)

    def make_parameter_CI_figures(self):
        """
        Returns a figure for each parameters that has confidence interval information
        """
        return plot_datasets.plot_parameter_ci(self.datafile.path, self.method)

    def get_system_parameters(self):
        """
        Returns a list of parameters that describe a property of the
        system, as for example orbital period or reddening.
        The list contains a tupple of (parameter name, unit, value+-error)
        for each parameter
        """
        parameters = self.parameter_set.filter(component__exact=SYSTEM)
        pars = []
        for p in parameters.order_by('name'):
            prec = PARAMETER_DECIMALS.get(p.name, 3)
            pars.append(
                (p.name, p.unit, "{: > 6.{prec}f} &pm; {: > 6.{prec}f}".format(p.rvalue(), p.rerror(), prec=prec)))
        return pars

    def get_component_parameters(self):
        """
        Returns a list of parameters that describe a property of one of
        the components of the system, as effective temperature or logg.
        The list contains a tupple of (parameter name, unit, v1+-e1, v2+-e2)
        for each parameter
        """
        parameters = set(
            self.parameter_set.filter(
                component__in=STELLAR_PARAMETERS
                ).values_list('name', flat=True)
            )
        pars = []
        for pname in parameters:
            # need to use filter here not get!
            qset = self.parameter_set.filter(name__exact=pname)

            line = [pname, qset[0].unit]
            for comp in STELLAR_PARAMETERS:
                p = qset.filter(component__exact=comp)

                if p:
                    prec = PARAMETER_DECIMALS.get(p[0].name, 3)
                    line.append(
                        "{: > 5.{prec}f} &pm; {: > 5.{prec}f}".format(p[0].rvalue(), p[0].rerror(), prec=prec)
                        )
                else:
                    line.append(r" / ")

            pars.append(tuple(line))
        return pars


@receiver(post_delete, sender=DataSet)
def dataSet_post_delete_handler(sender, **kwargs):
    analmethod = kwargs['instance']
    #   Check if the datafile is associated with another dataset. This might
    #   be the case after dataset updates. Remove datafile if that is not the
    #   case.
    same_datafile = DataSet.objects.all().filter(datafile=analmethod.datafile)
    if not same_datafile:
        storage, path = analmethod.datafile.storage, analmethod.datafile.path
        storage.delete(path)
