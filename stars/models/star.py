# from __future__ import unicode_literals

from astropy.coordinates.angles import Angle
from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
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
        pars = []

        for name in ['M_G', 'parallax', 'p', 't0', 'e']:
            p = self.parameter_set.filter(name__exact=name, average__exact=True)
            if len(p) > 0:
                p = p[0]
                pars.append((name, p.unit, "{} &pm; {}".format(p.rvalue(), p.rerror())))

        return pars

    def get_component_summary_parameter(self):
        """
        Returns a list of parameters that should be included in the
        summary part of the star.
        """
        pars = []

        for name in ['teff', 'logg', 'rad']:
            p1 = self.parameter_set.filter(name__exact=name, component__exact=1,
                                           average__exact=True)
            p2 = self.parameter_set.filter(name__exact=name, component__exact=2,
                                           average__exact=True)

            v1 = "{} &pm; {}".format(p1[0].rvalue(), p1[0].rerror()) if len(p1) > 0 else "/"
            v2 = "{} &pm; {}".format(p2[0].rvalue(), p2[0].rerror()) if len(p2) > 0 else "/"

            if len(p1) > 0 or len(p2) > 0:
                unit = p1[0].unit if len(p1) > 0 else p2[0].unit
                pars.append((name, unit, v1, v2))

        return pars

    # Generate .csv snippet of all parameters for specific source
    def parameter_csv(self):
        from analysis.models import COMPONENT_CHOICES, DataSource

        all_csv_dict = {}

        for source in DataSource.objects.all():
            params_from_source = self.parameter_set.filter(data_source__name__iexact=source.name)

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


@receiver(post_save, sender=Star)
def identifier_bookkeeping(sender, **kwargs):
    """
    Add identifiers when stars are created or star names are changed.
    For now identifiers are never automatically removed
    """

    if kwargs.get('raw', False):
        return

    star = kwargs['instance']

    # -- create an identifier with the same name as the star if non exist
    try:
        Identifier.objects.get(name__exact=star.name, star__exact=star)
    except Identifier.DoesNotExist:
        Identifier.objects.create(name=star.name, star=star)


@receiver(pre_save, sender=Identifier)
def identifier_add_project(sender, **kwargs):
    """
    Add the project of the star this belongs to to the identifier
    """

    identifier = kwargs['instance']
    identifier.project = identifier.star.project
