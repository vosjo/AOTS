from django.conf import settings
from django.db import models
from simple_history.models import HistoricalRecords
from six import python_2_unicode_compatible

from stars.models import Star
from users.models import get_sentinel_user

band_wavelengths = {'GALEX.FUV': 1535,
                    'GALEX.NUV': 2300,
                    'GAIA2.G': 6230,
                    'GAIA2.BP': 5050,
                    'GAIA2.RP': 7730,
                    'GAIA3.G': 5822.39,
                    'GAIA3.BP': 5035.75,
                    'GAIA3.RP': 7619.96,
                    'GAIA3.RVS': 8578.16,
                    'SKYMAP.U': 3490,
                    'SKYMAP.V': 3840,
                    'SKYMAP.G': 5100,
                    'SKYMAP.R': 6170,
                    'SKYMAP.I': 7790,
                    'SKYMAP.Z': 9160,
                    'APASS.B': 4303,
                    'APASS.V': 5437,
                    'APASS.G': 4718,
                    'APASS.R': 6185,
                    'APASS.I': 7499,
                    'SDSS.U': 3478,
                    'SDSS.G': 4795,
                    'SDSS.R': 6187,
                    'SDSS.I': 7658,
                    'SDSS.Z': 9668,
                    'PANSTAR.G': 4810,
                    'PANSTAR.R': 6170,
                    'PANSTAR.I': 7520,
                    'PANSTAR.Z': 8660,
                    'PANSTAR.Y': 9620,
                    '2MASS.J': 12393,
                    '2MASS.H': 16494,
                    '2MASS.K': 21638,
                    'WISE.W1': 33526,
                    'WISE.W2': 46028,
                    'WISE.W3': 115608,
                    'WISE.W4': 220883,
                    }


@python_2_unicode_compatible  # to support Python 2
class Photometry(models.Model):
    """
    A photometric measurement. We only save the observed value,
    values in other units like fluxes have to be calculated.
    There is no wavelength saved, only the bandname. Wavelength
    would then be redundant.
    """

    class Meta():
        ordering = ['wavelength', 'band']

    # -- a photometry measurement belongs to one star only
    star = models.ForeignKey(Star, on_delete=models.CASCADE)

    band = models.CharField(max_length=50)
    wavelength = models.FloatField(default=0)

    # -- measurement can be in any unit
    measurement = models.FloatField()
    error = models.FloatField()
    unit = models.CharField(max_length=50)

    # -- measurement can be an upper or lower limit on the actual flux
    upper_limit = models.BooleanField(default=False)
    lower_limit = models.BooleanField(default=False)

    # -- source to keep an article reference or reference to a vizier table
    source = models.TextField(default='')

    # -- bookkeeping
    history = HistoricalRecords()

    def get_value(self):
        if self.upper_limit:
            return "< {:0.3f}".format(self.measurement)
        if self.lower_limit:
            return "> {:0.3f}".format(self.measurement)
        return "{:0.3f}".format(self.measurement)

    def get_error(self):
        if self.upper_limit or self.lower_limit:
            return "/"
        else:
            return "{:0.3f}".format(self.error)

    # -- representation of self
    def __str__(self):
        if self.upper_limit:
            return "{} < {} {}".format(self.band, self.measurement, self.unit)
        if self.lower_limit:
            return "{} > {} {}".format(self.band, self.measurement, self.unit)
        return "{} = {} +- {} {}".format(self.band, self.measurement, self.error, self.unit)

    def save(self, *args, **kwargs):
        if self.band in band_wavelengths:
            self.wavelength = band_wavelengths[self.band]

        super(Photometry, self).save(*args, **kwargs)
