from django.db import models
from django.db.models.signals import pre_delete, post_delete, post_save, pre_save
from django.dispatch import receiver
from simple_history.models import HistoricalRecords

from analysis.auxil import parameter_derivation
from stars.models import Star, Project


class SED(models.Model):
    # -- an RVcurve belongs to one star only and is deleted when the star
    #   is deleted. However, a star can be added after creation.
    star = models.ForeignKey(Star, on_delete=models.CASCADE, blank=True, null=True)

    # -- an RVcurve belongs to a specific project
    #   when that project is deleted, the lightcurve is also deleted.
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=False, )

    teff = models.FloatField(default=0)
    logg = models.FloatField(default=0)
    metallicity = models.FloatField(default=0)

    instrument = models.CharField(max_length=200, default='')

    note = models.TextField(default='', blank=True)

    sourcefile = models.FileField(upload_to='SEDs/')

    # -- bookkeeping
    history = HistoricalRecords(cascade_delete_history=True)

    # -- representation of self
    def __str__(self):
        return f"SED for {self.star.name} with ...some parameters..."  # TODO:add these parameters here
