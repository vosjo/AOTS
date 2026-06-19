# from __future__ import unicode_literals

from astropy.coordinates.angles import Angle
from django.db import models
from simple_history.models import HistoricalRecords

from .project import Project


class Tag(models.Model):
    """
    A tag that can be added to a star to facilitate grouping
    """
    # -- Multiple stars can have the same tag, and multiple tags can be added to one star

    name = models.CharField(max_length=75)

    # -- a tag belongs to a specific project
    #   when that project is deleted, the star is also deleted.
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=False, )

    description = models.TextField(default='')

    color = models.CharField(max_length=7, default='#8B0000')  # color as hex color value

    # -- bookkeeping
    history = HistoricalRecords(cascade_delete_history=True)

    class Meta:
        ordering = ['name']

    # -- representation of self
    def __str__(self):
        return "{}:{}".format(self.name, self.description)


class Star(models.Model):
    name = models.CharField(max_length=200)

    # -- a star belongs to a specific project
    #   when that project is deleted, the star is also deleted.
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=False, )

    # -- coordinates in decimal form
    ra = models.FloatField()
    dec = models.FloatField()

    # -- spectral classification
    classification = models.CharField(max_length=50, blank=True)

    SPECTROSCOPIC = 'SP'
    PHOTOMETRIC = 'PH'
    CLASSIFICATION_TYPE_CHOICES = (
        (SPECTROSCOPIC, 'Spectroscopic'),
        (PHOTOMETRIC, 'Photometric'),)

    classification_type = models.CharField(
        max_length=2,
        choices=CLASSIFICATION_TYPE_CHOICES,
        default=PHOTOMETRIC)

    # -- observing
    FINISHED = 'FI'
    ONGOING = 'ON'
    REJECTED = 'RE'
    NEW = 'NE'
    OBSERVING_STATUS_CHOICES = (
        (FINISHED, 'Finished'),
        (ONGOING, 'Ongoing'),
        (REJECTED, 'Rejected'),
        (NEW, 'New'))
    observing_status = models.CharField(
        max_length=2,
        choices=OBSERVING_STATUS_CHOICES,
        default=NEW)

    note = models.TextField(default='', blank=True)

    # -- tags
    tags = models.ManyToManyField(Tag, related_name='stars', blank=True)

    # -- bookkeeping
    history = HistoricalRecords(cascade_delete_history=True)

    def get_system_summary_parameter(self):
        """
        Returns a list of parameters that should be included in the
        summary part of the star.
        """
        from analysis.services.parameter_consensus import (
            consensus_provenance_display,
            get_consensus_parameter,
        )

        pars = []

        for name in ['absolute_g_mag', 'parallax', 'p', 't0', 'e']:
            p = get_consensus_parameter(self, name, component=0)
            if p is not None:
                provenance = consensus_provenance_display(self, p, name, component=0)
                pars.append((name, p.unit, "{} &pm; {}".format(p.rvalue(), p.rerror()), provenance))

        return pars

    def get_component_summary_parameter(self):
        """
        Returns a list of parameters that should be included in the
        summary part of the star.
        """
        from analysis.services.parameter_consensus import (
            consensus_provenance_display,
            get_consensus_parameter,
        )

        pars = []

        for name in ['teff', 'logg', 'rad']:
            p1 = get_consensus_parameter(self, name, component=1)
            p2 = get_consensus_parameter(self, name, component=2)

            v1 = "{} &pm; {}".format(p1.rvalue(), p1.rerror()) if p1 is not None else "/"
            v2 = "{} &pm; {}".format(p2.rvalue(), p2.rerror()) if p2 is not None else "/"

            if p1 is not None or p2 is not None:
                unit = p1.unit if p1 is not None else p2.unit
                ref = p1 if p1 is not None else p2
                provenance = consensus_provenance_display(self, ref, name, component=ref.component)
                pars.append((name, unit, v1, v2, provenance))

        return pars

    # Generate .csv snippet of all parameters for specific source
    def parameter_csv(self):
        from analysis.models import COMPONENT_CHOICES, ParameterSource

        all_csv_dict = {}

        for source in ParameterSource.objects.filter(project=self.project):
            params_from_source = self.parameter_set.filter(parameter_source__name__iexact=source.name)

            csv_dict = {}
            for p in params_from_source:
                choices_dict = {}
                for key, val in COMPONENT_CHOICES:
                    choices_dict[key] = val
                comp = choices_dict[p.component]
                csv_dict[f"{comp}_{p.name}"] = str(p.value)
                csv_dict[f"{comp}_{p.name}_err"] = str(p.error)

            all_csv_dict[source.name.replace(" ", "_")] = ",".join([*(csv_dict.keys())]) + "\n" + ",".join([*(csv_dict.values())])
        return all_csv_dict

    # -- hms and dms representation for ra and dec
    def ra_hms(self):
        try:
            a = Angle(float(self.ra), unit='degree').hms
        except Exception as e:
            return self.ra
        return "{:02.0f}:{:02.0f}:{:05.2f}".format(*a)

    def dec_dms(self):
        try:
            a = Angle(float(self.dec), unit='degree').dms
        except Exception as e:
            return self.dec
        return "{:+03.0f}:{:02.0f}:{:05.2f}".format(a[0], abs(a[1]), abs(a[2]))

    # -- representation of self
    def __str__(self):
        return "{}: {:.2f} {:.2f}".format(self.name, self.ra, self.dec)


class Identifier(models.Model):
    """
    An alternative name for a star
    """
    # -- Altnames should be removed when the star is removed
    star = models.ForeignKey(Star, on_delete=models.CASCADE)

    # -- an identifier belongs to a specific project
    #   when that project is deleted, the identiefers are also deleted.
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=False, )

    name = models.CharField(max_length=200)

    href = models.CharField(max_length=400, blank=True)

    # -- bookkeeping
    history = HistoricalRecords(cascade_delete_history=True)

    # -- representation of self
    def __str__(self):
        return "{} = {} ; {}".format(self.star.name, self.name, self.href)

    def save(self, *args, **kwargs):
        if self.star_id:
            self.project = self.star.project
        super().save(*args, **kwargs)
