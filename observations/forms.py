# import re
# import datetime

from django import forms

from stars.forms import RAField, DecField
from stars.models import Star
from .models import Observatory, SpecFile


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


# ===========================================================================================
#  SPECFILE
# ===========================================================================================

class UploadSpectraDetailForm(forms.Form):
    #   File
    spectrumfile = MultipleFileField(label='Please select the spectra...')

    # merge_spectra_if_possible = forms.BooleanField(required=False)

    #   Add info provided by the user?
    add_info = forms.BooleanField(initial=False, required=False)

    #   File type
    filetype = forms.CharField(max_length=50, required=False)

    #   Target
    objectname = forms.CharField(max_length=50, required=False)
    ra = RAField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '  h:m:s or d.d°'}),
    )
    dec = DecField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '  ° : \' : \'\' or d.d°'}),
    )
    create_new_star = forms.BooleanField(initial=True, required=False)
    classification = forms.CharField(max_length=50, required=False)
    classification_type = forms.ChoiceField(
        choices=(
            ('SP', 'Spectroscopic'),
            ('PH', 'Photometric'),
        ),
        initial='PH',
        required=False,
    )

    #   Observatory
    observatory = forms.ModelChoiceField(
        queryset=Observatory.objects.all(),
        required=False,
    )
    observatory_name = forms.CharField(max_length=100, required=False)
    observatory_latitude = forms.FloatField(required=False)
    observatory_longitude = forms.FloatField(required=False)
    observatory_altitude = forms.FloatField(required=False)
    observatory_is_spacecraft = forms.BooleanField(required=False)

    #   Instrument and setup
    telescope = forms.CharField(max_length=200, required=False)
    instrument = forms.CharField(max_length=200, required=False)
    hjd = forms.FloatField(required=False)
    exptime = forms.FloatField(required=False)
    resolution = forms.FloatField(required=False)
    snr = forms.FloatField(required=False)
    observer = forms.CharField(max_length=50, required=False)

    #   Observing conditions
    wind_speed = forms.FloatField(required=False)
    wind_direction = forms.FloatField(required=False)
    seeing = forms.FloatField(required=False)
    airmass = forms.FloatField(required=False)

    #   Normalized
    normalized = forms.BooleanField(required=False)

    #   Barycentric Correction
    # barycor      = forms.FloatField(required=False)
    barycor_bool = forms.BooleanField(required=False, initial=True)

    #   Flux info
    fluxcal = forms.BooleanField(required=False)
    flux_units = forms.CharField(max_length=50, required=False)

    #   Master and/or decomposed spectrum
    master = forms.BooleanField(required=False)
    decomposed = forms.BooleanField(required=False)

    #   Note
    note = forms.CharField(
        widget=forms.Textarea(attrs={'cols': 70, 'rows': 10}),
        required=False,
    )


# class UploadSpecFileForm(forms.Form):
#     specfile_field = forms.FileField(
#         label='Select a spectrum',
#         widget=forms.ClearableFileInput(
#             attrs={'allow_multiple_selected': True}
#             )
#     )


class UploadRawSpecFileForm(forms.Form):
    """
        Upload form for spectroscopic raw data
    """

    system_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form_long'}),
        required=False,
    )

    system = forms.ModelMultipleChoiceField(
        label='Systems',
        queryset=Star.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form_long_extra'}),
        required=False,
    )

    specfile_date = forms.DateTimeField(
        label='Observation date',
        widget=forms.TextInput(attrs={'class': 'form_long'}),
        required=False,
    )

    specfile = forms.ModelMultipleChoiceField(
        label='Spectra',
        queryset=SpecFile.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form_long_extra'}),
        # required=True,
        required=False,
    )

    #   Raw file upload field
    raw_files = MultipleFileField(label='Raw files')


class PatchRawSpecFileForm(forms.Form):
    """
        Patch form for spectroscopic raw data
    """
    system_name_patch = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form_long'}),
        required=False,
    )

    system_patch = forms.ModelMultipleChoiceField(
        label='Systems',
        queryset=Star.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form_long_extra'}),
        required=False,
    )

    specfile_date_patch = forms.DateTimeField(
        label='Observation date',
        widget=forms.TextInput(attrs={'class': 'form_long'}),
        required=False,
    )

    specfile_patch = forms.ModelMultipleChoiceField(
        label='Spectra',
        queryset=SpecFile.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form_long_extra'}),
        required=True,
    )


class OrderField(forms.IntegerField):
    """
        Specific form field for the polynomial order
    """

    def validate(self, value):
        #   Use the parent's handling of integer fields
        super().validate(value)
        #   Add specific handling
        if value is not None and value > 15:
            raise forms.ValidationError("More than 15 orders are not supported")


class BinningField(forms.IntegerField):
    """
        Specific form field for the polynomial order
    """

    def validate(self, value):
        #   Use the parent's handling of integer fields
        super().validate(value)
        #   Add specific handling
        if value is not None and value > 100:
            raise forms.ValidationError("Binning of > 100 is not supported")
        # if value != None and value == 0:
        # raise forms.ValidationError("Binning of 0 makes no sense")


class SpectrumModForm(forms.Form):
    """
        Form to customize spectral plots (on the detail page)
    """
    normalize = forms.BooleanField(label="Normalize", required=False)
    order = OrderField(label="Polynomial order", required=False)
    binning = BinningField(label="Select a binning", required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['order'] = 3
        self.initial['binning'] = 10


# ===========================================================================================
#  LICHT CURVES
# ===========================================================================================

class UploadLightCurveForm(forms.Form):
    lcfile = MultipleFileField(label='Select light curves')


# ===========================================================================================
#  OBSERVATORIES
# ===========================================================================================

class UpdateObservatoryForm(forms.Form):
    pk = forms.IntegerField(required=True)
    name = forms.CharField(max_length=50, required=True)
    short_name = forms.CharField(max_length=50, required=True)
    telescopes = forms.CharField(max_length=50, required=False)
    latitude = forms.FloatField(required=True)
    longitude = forms.FloatField(required=True)
    altitude = forms.FloatField(required=False)
    space_craft = forms.BooleanField(label="Space Craft", required=False)
    note = forms.CharField(max_length=150, required=False)
    url = forms.CharField(max_length=150, required=False)
    weatherurl = forms.CharField(max_length=150, required=False)
