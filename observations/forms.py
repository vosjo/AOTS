# import re
# import datetime

from .models import Observatory, SpecFile

from stars.models import Star

from django import forms

from stars.forms import RAField, DecField


# ===========================================================================================
#  SPECFILE
# ===========================================================================================

class UploadSpectraDetailForm(forms.Form):
    #   File
    spectrumfile = forms.FileField(
        label='Select a spectrum',
        widget=forms.ClearableFileInput(attrs={'multiple': True}),
    )
    # merge_spectra_if_possible = forms.BooleanField(required=False)

    #   Add infos provided by the user?
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

    #   Note
    note = forms.CharField(
        widget=forms.Textarea(attrs={'cols': 70, 'rows': 10}),
        required=False,
    )


class UploadSpecFileForm(forms.Form):
    specfile_field = forms.FileField(
        label='Select a spectrum',
        widget=forms.ClearableFileInput(attrs={'multiple': True})
    )


class UploadRawSpecFileForm(forms.Form):
    '''
        Upload form for spectroscopic raw data
    '''
    system = forms.ModelMultipleChoiceField(
        label='Systems',
        # empty_label='Target name: ra[deg] dec[deg]',
        queryset=Star.objects.all(),
        required=False,
    )

    specfile = forms.ModelMultipleChoiceField(
        label='Spectra',
        # empty_label='HJD@Instrument - Filetype',
        queryset=SpecFile.objects.all(),
        required=True,
    )

    #   Raw file upload field
    rawfile = forms.FileField(
        label='Raw files',
        widget=forms.ClearableFileInput(attrs={'multiple': True})
    )


class PatchRawSpecFileForm(forms.Form):
    '''
        Patch form for spectroscopic raw data
    '''
    system_patch = forms.ModelMultipleChoiceField(
        label='Systems',
        # empty_label='Target name: ra[deg] dec[deg]',
        queryset=Star.objects.all(),
        required=False,
    )

    specfile_patch = forms.ModelMultipleChoiceField(
        label='Spectra',
        # empty_label='HJD@Instrument - Filetype',
        queryset=SpecFile.objects.all(),
        required=True,
    )


class OrderField(forms.IntegerField):
    '''
        Specific form field for the polynomial order
    '''

    def validate(self, value):
        #   Use the parent's handling of integer fields
        super().validate(value)
        #   Add specific handling
        if value != None and value > 15:
            raise forms.ValidationError("More than 15 orders are not supported")


class BinningField(forms.IntegerField):
    '''
        Specific form field for the polynomial order
    '''

    def validate(self, value):
        #   Use the parent's handling of integer fields
        super().validate(value)
        #   Add specific handling
        if value != None and value > 100:
            raise forms.ValidationError("Binning of > 100 is not supported")
        # if value != None and value == 0:
        # raise forms.ValidationError("Binning of 0 makes no sense")


class SpectrumModForm(forms.Form):
    '''
        Form to customize spectral plots (on the detail page)
    '''
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
    lcfile = forms.FileField(label='Select a light curve',
                             widget=forms.ClearableFileInput(attrs={'multiple': True}))


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
