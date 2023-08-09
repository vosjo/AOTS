from django.db import models
from django.db.models.signals import pre_delete, post_delete, post_save, pre_save
from django.dispatch import receiver
from simple_history.models import HistoricalRecords

from analysis.auxil import parameter_derivation
from stars.models import Star, Project


class RVcurve(models.Model):
    # -- an RVcurve belongs to one star only and is deleted when the star
    #   is deleted. However, a star can be added after creation.
    star = models.ForeignKey(Star, on_delete=models.CASCADE, blank=True, null=True)

    # -- an RVcurve belongs to a specific project
    #   when that project is deleted, the lightcurve is also deleted.
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=False, )

    time_spanned = models.FloatField(default=0)  # duration from first to last measurement
    N_samples = models.FloatField(default=0)  # number of samples

    average_rv = models.FloatField(default=0)  # average value of the RV curve
    average_rv_err = models.FloatField(default=0)

    delta_rv = models.FloatField(default=0) # delta of highest to lowest rv values
    delta_rv_err = models.FloatField(default=0) # delta of highest to lowest rv values

    half_amplitude = models.FloatField(default=0)  # half-amplitude K of the RV curve from orbital solution
    half_amplitude_err = models.FloatField(default=0)

    logp = models.FloatField(default=0)  # false-detection probability log p

    solved = models.BooleanField(default=False)

    note = models.TextField(default='', blank=True)

    sourcefile = models.FileField(upload_to='rvcurves/')

    # -- bookkeeping
    history = HistoricalRecords(cascade_delete_history=True)

    # -- representation of self
    def __str__(self):
        return f"RV_curve for {self.star.name} with K={self.half_amplitude} and log(p)={self.logp}"