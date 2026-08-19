from django.db import models
from simple_history.models import HistoricalRecords

from stars.models import Star
from stars.photometry_bands import BAND_WAVELENGTHS as band_wavelengths


class Photometry(models.Model):
    """
    A photometric measurement. We only save the observed value,
    values in other units like fluxes have to be calculated.
    There is no wavelength saved, only the bandname. Wavelength
    would then be redundant.
    """

    class Meta:
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
    history = HistoricalRecords(cascade_delete_history=True)

    def get_value(self):
        if self.upper_limit:
            return f"< {self.measurement:0.3f}"
        if self.lower_limit:
            return f"> {self.measurement:0.3f}"
        return f"{self.measurement:0.3f}"

    def get_error(self):
        if self.upper_limit or self.lower_limit:
            return "/"
        else:
            return f"{self.error:0.3f}"

    # -- representation of self
    def __str__(self):
        if self.upper_limit:
            return f"{self.band} < {self.measurement} {self.unit}"
        if self.lower_limit:
            return f"{self.band} > {self.measurement} {self.unit}"
        return f"{self.band} = {self.measurement} +- {self.error} {self.unit}"

    def save(self, *args, **kwargs):
        if self.band in band_wavelengths:
            self.wavelength = band_wavelengths[self.band]

        super().save(*args, **kwargs)
