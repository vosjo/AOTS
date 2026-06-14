from __future__ import unicode_literals

from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from simple_history.models import HistoricalRecords

from analysis.auxil import plot_analyses
from analysis.categories import AnalysisCategory, CategorySource, category_label
from stars.models import Star, Project
from .default_values import *


class Analysis(models.Model):
    """HDF5 analysis result (RV, SED fit, etc.) — standalone, not a parameter source."""

    id = models.AutoField(primary_key=True, db_column='datasource_ptr_id')

    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=False)
    name = models.TextField(default='')
    note = models.TextField(default='')
    reference = models.TextField(default='')

    star = models.ForeignKey(Star, on_delete=models.CASCADE, blank=True, null=True)

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

    datafile = models.FileField(upload_to='datasets/')
    fit = models.BooleanField(default=True)

    history = HistoricalRecords(cascade_delete_history=True)

    class Meta:
        db_table = 'analysis_analysis'

    def get_category_display(self):
        return category_label(self.category)

    def get_reference_url(self):
        if self.reference != '':
            return 'http://adsabs.harvard.edu/abs/' + self.reference
        return ''

    def __str__(self):
        return "{} {}".format(self.name, '({})'.format(self.reference) if self.reference else '')

    def get_data(self):
        from analysis.services.analysis_io import read_analysis_data
        return read_analysis_data(self)

    def make_figure(self):
        return plot_analyses.plot_analysis(self.datafile.path, self.category)

    def make_large_figure(self):
        return plot_analyses.plot_analysis_large(self.datafile.path, self.category)

    def make_OC_figure(self):
        return plot_analyses.plot_analysis_oc(self.datafile.path, self.category)

    def make_parameter_hist_figures(self):
        return plot_analyses.plot_generic_hist(self.datafile.path)

    def make_parameter_CI_figures(self):
        return plot_analyses.plot_parameter_ci(self.datafile.path, self.category)

    def get_system_parameters(self):
        from .parameters import Parameter
        parameters = Parameter.objects.filter(analysis=self, component__exact=SYSTEM)
        pars = []
        for p in parameters.order_by('name'):
            prec = PARAMETER_DECIMALS.get(p.name, 3)
            pars.append(
                (p.name, p.unit, "{: > 6.{prec}f} &pm; {: > 6.{prec}f}".format(p.rvalue(), p.rerror(), prec=prec)))
        return pars

    def get_component_parameters(self):
        from .parameters import Parameter
        parameters = set(
            Parameter.objects.filter(
                analysis=self,
                component__in=STELLAR_PARAMETERS,
            ).values_list('name', flat=True)
        )
        pars = []
        for pname in parameters:
            qset = Parameter.objects.filter(analysis=self, name__exact=pname)

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


@receiver(post_delete, sender=Analysis)
def analysis_post_delete_handler(sender, **kwargs):
    analysis = kwargs['instance']
    same_datafile = Analysis.objects.filter(datafile=analysis.datafile)
    if not same_datafile.exists():
        storage, path = analysis.datafile.storage, analysis.datafile.path
        storage.delete(path)
