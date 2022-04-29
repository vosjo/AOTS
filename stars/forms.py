import re

from astropy.coordinates.angles import Angle
from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q

from .models import Star, Tag


class RAField(forms.CharField):
    """
        Custom field to input Right Ascention (RA) in hexadecimal form in hours.
    """

    errormessage = 'Cannot interpret RA angle, try format: hh:mm:ss.ss, hh mm ss.ss or dd.ddddd'

    def clean(self, value):
        if not value:
            return None
        value = value.strip()

        #   Check if a decimal or hexadecimal number was given
        if re.match('^\d+\.\d+$', value) or re.match('^\d+\.+$', value):
            if float(value) > 360 or float(value) < 0:
                raise ValidationError(self.errormessage, code='invalid_ra')
            else:
                return float(value)
        else:
            try:
                return Angle(value.strip(), unit='hour').degree
            except:
                raise ValidationError(self.errormessage, code='invalid_ra')


class DecField(forms.CharField):
    """
        Custom field to input Declination (Dec) in hexadecimal form in hours.
    """

    errormessage = 'Cannot interpret Dec angle, try format: dd:mm:ss.ss, dd mm ss.ss or dd.ddddd'

    def clean(self, value):
        if not value:
            return None

        value = value.strip()

        #   Check if a decimal or hexadecimal number was given
        if re.match('^\d+\.\d+$', value) or re.match('^\d+\.+$', value):
            if float(value) < -90 or float(value) > 90:
                raise ValidationError(self.errormessage, code='invalid_dec')
            else:
                return float(value)
        else:
            try:
                return Angle(value.strip(), unit='degree').degree
            except:
                raise ValidationError(self.errormessage, code='invalid_dec')


# ==================================================================================
# STAR related forms
# ==================================================================================

class RangeField(forms.CharField):
    """
        A char field in which you can specify a range by using the ':' character
        which returns the range as a tuple of floats
    """

    def to_python(self, value):
        """ Normalize the data to a tuple of floats """
        if not value or value == '':
            return None
        if not ':' in value:
            raise forms.ValidationError(
                "Please provide a range using ':'.",
                code='no_range',
            )
        else:
            try:
                value = value.strip().split(':')
                return (float(value[0]), float(value[1]))
            except Exception as e:
                raise forms.ValidationError(
                    'Cannot interpret provided range',
                    code='invalid_range',
                )


class FilterStarForm(forms.Form):
    ra = RangeField(
        label="Ra: ",
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'filter-input', 'placeholder': 'min:max'}
        ),
    )

    dec = RangeField(
        label="Dec: ",
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'filter-input', 'placeholder': 'min:max'}
        ),
    )

    mag = RangeField(
        label="V-mag: ",
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'filter-input', 'placeholder': 'min:max'}
        ),
    )

    status = forms.MultipleChoiceField(
        label="Status: ",
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    classification = forms.MultipleChoiceField(
        label="Class: ",
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    tag = forms.MultipleChoiceField(
        label="Tags: ",
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    def clean(self):
        cd = self.cleaned_data
        if 'ra' in cd and cd['ra'] == None:
            self.cleaned_data.pop('ra')
        if 'dec' in cd and cd['dec'] == None:
            self.cleaned_data.pop('dec')
        if 'mag' in cd and cd['mag'] == None:
            self.cleaned_data.pop('mag')

        if (not 'ra' in self.cleaned_data and
                not 'dec' in self.cleaned_data and
                self.cleaned_data['status'] == [] and
                self.cleaned_data['tag'] == []):
            raise forms.ValidationError("You should at least filter one thing")

        return self.cleaned_data

    def filter_stars(self):
        ra = self.cleaned_data.get('ra', (0, 24))
        #   Convert from hours to degrees
        ra = (ra[0] / 24. * 360, ra[1] / 24. * 360)
        dec = self.cleaned_data.get('dec', (-90, 90))

        all_stars = Star.objects.filter(ra__range=ra, dec__range=dec)

        #   Filter on Status
        if len(self.cleaned_data['status']) > 0:
            stat = self.cleaned_data['status']
            all_stars = all_stars & Star.objects.filter(observing_status__in=stat)

        #   Filter on Tag
        if len(self.cleaned_data['tag']) > 0:
            tags = self.cleaned_data['tag']
            all_stars = all_stars & Star.objects.filter(tag__pk__in=tags)

        return all_stars.order_by('ra')


class SearchStarForm(forms.Form):
    """
        Form for searching stars on name, classification and tag. The search_
        stars function returns a queryset containing all stars fullfiling the
        search criterium
    """

    q = forms.CharField(
        label='Search',
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'small-text', 'placeholder': 'Search'}
        ),
    )

    def search(self):
        val = self.cleaned_data['q']
        if val == '':
            return Star.objects.order_by('ra')

        #   Search on name, class and tag name
        all_stars = Star.objects.filter(Q(name__icontains=val) |
                                        Q(classification__icontains=val) |
                                        Q(tag__name__icontains=val))

        return all_stars.order_by('ra').distinct()


class StarForm(forms.ModelForm):
    """
        https://docs.djangoproject.com/en/1.10/topics/forms/modelforms/
    """

    ra = RAField()
    dec = DecField()

    class Meta:
        model = Star

        fields = ['name', 'ra', 'dec', 'classification', 'classification_type',
                  'observing_status']

        widgets = {
            'note': forms.Textarea(attrs={'cols': 80, 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super(StarForm, self).__init__(*args, **kwargs)
        #   Some fields are not required
        self.fields['classification'].required = False
        self.fields['classification_type'].required = False


# ===========================================================================================
#  SYSTEMS
# ===========================================================================================


class UploadSystemForm(forms.Form):
    system = forms.FileField(label='Select a System')


class UploadSystemDetailForm(forms.Form):
    #   Target name
    main_id = forms.CharField(max_length=50, required=True)

    #   Download from Simbad/Vizier?
    get_simbad = forms.BooleanField(initial=False, required=False)

    #   Coordinates
    ra = RAField(
        max_length=20,
        # required=True,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '  h:m:s or d.d°'}),
    )
    dec = DecField(
        max_length=20,
        # required=True,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '  ° : \' : \'\' or d.d°'}),
    )

    #   Spectral type
    sp_type = forms.CharField(max_length=30, required=False)
    classification_type = forms.ChoiceField(
        choices=(
            ('SP', 'Spectroscopic'),
            ('PH', 'Photometric'),
        ),
        initial='PH',
        required=False,
    )

    #   Parallax
    parallax = forms.FloatField(required=False)
    parallax_error = forms.FloatField(required=False)

    #   Proper motion
    pmra_x = forms.FloatField(required=False)
    pmra_error = forms.FloatField(required=False)
    pmdec_x = forms.FloatField(required=False)
    pmdec_error = forms.FloatField(required=False)

    #   Gaia photometry and Errors
    phot_g_mean_mag = forms.FloatField(required=False)
    phot_bp_mean_mag = forms.FloatField(required=False)
    phot_rp_mean_mag = forms.FloatField(required=False)
    phot_g_mean_magerr = forms.FloatField(required=False)
    phot_bp_mean_magerr = forms.FloatField(required=False)
    phot_rp_mean_magerr = forms.FloatField(required=False)

    #   JHK photometry and Errors
    Jmag = forms.FloatField(required=False)
    Hmag = forms.FloatField(required=False)
    Kmag = forms.FloatField(required=False)
    Jmagerr = forms.FloatField(required=False)
    Hmagerr = forms.FloatField(required=False)
    Kmagerr = forms.FloatField(required=False)

    #   WISE photometry and Errors
    W1mag = forms.FloatField(required=False)
    W2mag = forms.FloatField(required=False)
    W3mag = forms.FloatField(required=False)
    W4mag = forms.FloatField(required=False)
    W1magerr = forms.FloatField(required=False)
    W2magerr = forms.FloatField(required=False)
    W3magerr = forms.FloatField(required=False)
    W4magerr = forms.FloatField(required=False)

    # UV(Galex) photometry and Errors
    FUV = forms.FloatField(required=False)
    NUV = forms.FloatField(required=False)
    FUVerr = forms.FloatField(required=False)
    NUVerr = forms.FloatField(required=False)

    # SKYMAP photometry and Errors
    Umag = forms.FloatField(required=False)
    Vmag = forms.FloatField(required=False)
    Gmag = forms.FloatField(required=False)
    Rmag = forms.FloatField(required=False)
    Imag = forms.FloatField(required=False)
    Zmag = forms.FloatField(required=False)
    Umagerr = forms.FloatField(required=False)
    Vmagerr = forms.FloatField(required=False)
    Gmagerr = forms.FloatField(required=False)
    Rmagerr = forms.FloatField(required=False)
    Imagerr = forms.FloatField(required=False)
    Zmagerr = forms.FloatField(required=False)

    # APASS photometry and Errors
    APBmag = forms.FloatField(required=False)
    APVmag = forms.FloatField(required=False)
    APGmag = forms.FloatField(required=False)
    APRmag = forms.FloatField(required=False)
    APImag = forms.FloatField(required=False)
    APBmagerr = forms.FloatField(required=False)
    APVmagerr = forms.FloatField(required=False)
    APGmagerr = forms.FloatField(required=False)
    APRmagerr = forms.FloatField(required=False)
    APImagerr = forms.FloatField(required=False)

    # SDSS photometry and Errors
    SDSSUmag = forms.FloatField(required=False)
    SDSSGmag = forms.FloatField(required=False)
    SDSSRmag = forms.FloatField(required=False)
    SDSSImag = forms.FloatField(required=False)
    SDSSZmag = forms.FloatField(required=False)
    SDSSUmagerr = forms.FloatField(required=False)
    SDSSGmagerr = forms.FloatField(required=False)
    SDSSRmagerr = forms.FloatField(required=False)
    SDSSImagerr = forms.FloatField(required=False)
    SDSSZmagerr = forms.FloatField(required=False)

    # PANSTAR photometry and Errors
    PANGmag = forms.FloatField(required=False)
    PANRmag = forms.FloatField(required=False)
    PANImag = forms.FloatField(required=False)
    PANZmag = forms.FloatField(required=False)
    PANYmag = forms.FloatField(required=False)
    PANGmagerr = forms.FloatField(required=False)
    PANRmagerr = forms.FloatField(required=False)
    PANImagerr = forms.FloatField(required=False)
    PANZmagerr = forms.FloatField(required=False)
    PANYmagerr = forms.FloatField(required=False)

    tags = forms.ModelMultipleChoiceField(
        label='Tags',
        queryset=Tag.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    INSTRUMENTS = (
        ('APASS', 'APASS'),
        ('SKYMAP', 'SKYMAP'),
        ('SDSS', 'SDSS'),
        ('PANSTAR', 'PANSTAR'),
        ('JHKWISE', 'JHK and WISE'),
        ('GALEX', 'Galex'),
    )

    instrument = forms.CharField(widget=forms.Select(choices=INSTRUMENTS))


# ===========================================================================================
#   SYSTEM DETAIL PHOTOMETRY
# ===========================================================================================


class UpdatePhotometryForm(forms.Form):
    #   Gaia photometry and Errors
    phot_g_mean_mag = forms.FloatField(required=False, label='GAIA2.G', show_hidden_initial=True)
    phot_bp_mean_mag = forms.FloatField(required=False, label='GAIA2.BP', show_hidden_initial=True)
    phot_rp_mean_mag = forms.FloatField(required=False, label='GAIA2.RP', show_hidden_initial=True)
    phot_g_mean_magerr = forms.FloatField(required=False, label='GAIA2.Gerr', show_hidden_initial=True)
    phot_bp_mean_magerr = forms.FloatField(required=False, label='GAIA2.BPerr', show_hidden_initial=True)
    phot_rp_mean_magerr = forms.FloatField(required=False, label='GAIA2.RPerr', show_hidden_initial=True)

    #   JHK photometry and Errors
    Jmag = forms.FloatField(required=False, label='2MASS.J', show_hidden_initial=True)
    Hmag = forms.FloatField(required=False, label='2MASS.H', show_hidden_initial=True)
    Kmag = forms.FloatField(required=False, label='2MASS.K', show_hidden_initial=True)
    Jmagerr = forms.FloatField(required=False, label='2MASS.Jerr', show_hidden_initial=True)
    Hmagerr = forms.FloatField(required=False, label='2MASS.Herr', show_hidden_initial=True)
    Kmagerr = forms.FloatField(required=False, label='2MASS.Kerr', show_hidden_initial=True)

    #   WISE photometry and Errors
    W1mag = forms.FloatField(required=False, label='WISE.W1', show_hidden_initial=True)
    W2mag = forms.FloatField(required=False, label='WISE.W2', show_hidden_initial=True)
    W3mag = forms.FloatField(required=False, label='WISE.W3', show_hidden_initial=True)
    W4mag = forms.FloatField(required=False, label='WISE.W4', show_hidden_initial=True)
    W1magerr = forms.FloatField(required=False, label='WISE.W1err', show_hidden_initial=True)
    W2magerr = forms.FloatField(required=False, label='WISE.W2err', show_hidden_initial=True)
    W3magerr = forms.FloatField(required=False, label='WISE.W3err', show_hidden_initial=True)
    W4magerr = forms.FloatField(required=False, label='WISE.W4err', show_hidden_initial=True)

    # UV(Galex) photometry and Errors
    FUV = forms.FloatField(required=False, label='GALEX.FUV', show_hidden_initial=True)
    NUV = forms.FloatField(required=False, label='GALEX.NUV', show_hidden_initial=True)
    FUVerr = forms.FloatField(required=False, label='GALEX.FUVerr', show_hidden_initial=True)
    NUVerr = forms.FloatField(required=False, label='GALEX.NUVerr', show_hidden_initial=True)

    # SKYMAP photometry and Errors
    Umag = forms.FloatField(required=False, label='SKYMAP.U', show_hidden_initial=True)
    Vmag = forms.FloatField(required=False, label='SKYMAP.V', show_hidden_initial=True)
    Gmag = forms.FloatField(required=False, label='SKYMAP.G', show_hidden_initial=True)
    Rmag = forms.FloatField(required=False, label='SKYMAP.R', show_hidden_initial=True)
    Imag = forms.FloatField(required=False, label='SKYMAP.I', show_hidden_initial=True)
    Zmag = forms.FloatField(required=False, label='SKYMAP.Z', show_hidden_initial=True)
    Umagerr = forms.FloatField(required=False, label='SKYMAP.Uerr', show_hidden_initial=True)
    Vmagerr = forms.FloatField(required=False, label='SKYMAP.Verr', show_hidden_initial=True)
    Gmagerr = forms.FloatField(required=False, label='SKYMAP.Gerr', show_hidden_initial=True)
    Rmagerr = forms.FloatField(required=False, label='SKYMAP.Rerr', show_hidden_initial=True)
    Imagerr = forms.FloatField(required=False, label='SKYMAP.Ierr', show_hidden_initial=True)
    Zmagerr = forms.FloatField(required=False, label='SKYMAP.Zerr', show_hidden_initial=True)

    # APASS photometry and Errors
    APBmag = forms.FloatField(required=False, label='APASS.B', show_hidden_initial=True)
    APVmag = forms.FloatField(required=False, label='APASS.V', show_hidden_initial=True)
    APGmag = forms.FloatField(required=False, label='APASS.G', show_hidden_initial=True)
    APRmag = forms.FloatField(required=False, label='APASS.R', show_hidden_initial=True)
    APImag = forms.FloatField(required=False, label='APASS.I', show_hidden_initial=True)
    APBmagerr = forms.FloatField(required=False, label='APASS.Berr', show_hidden_initial=True)
    APVmagerr = forms.FloatField(required=False, label='APASS.Verr', show_hidden_initial=True)
    APGmagerr = forms.FloatField(required=False, label='APASS.Gerr', show_hidden_initial=True)
    APRmagerr = forms.FloatField(required=False, label='APASS.Rerr', show_hidden_initial=True)
    APImagerr = forms.FloatField(required=False, label='APASS.Ierr', show_hidden_initial=True)

    # SDSS photometry and Errors
    SDSSUmag = forms.FloatField(required=False, label='SDSS.U', show_hidden_initial=True)
    SDSSGmag = forms.FloatField(required=False, label='SDSS.G', show_hidden_initial=True)
    SDSSRmag = forms.FloatField(required=False, label='SDSS.R', show_hidden_initial=True)
    SDSSImag = forms.FloatField(required=False, label='SDSS.I', show_hidden_initial=True)
    SDSSZmag = forms.FloatField(required=False, label='SDSS.Z', show_hidden_initial=True)
    SDSSUmagerr = forms.FloatField(required=False, label='SDSS.Uerr', show_hidden_initial=True)
    SDSSGmagerr = forms.FloatField(required=False, label='SDSS.Gerr', show_hidden_initial=True)
    SDSSRmagerr = forms.FloatField(required=False, label='SDSS.Rerr', show_hidden_initial=True)
    SDSSImagerr = forms.FloatField(required=False, label='SDSS.Ierr', show_hidden_initial=True)
    SDSSZmagerr = forms.FloatField(required=False, label='SDSS.Zerr', show_hidden_initial=True)

    # PANSTAR photometry and Errors
    PANGmag = forms.FloatField(required=False, label='PANSTAR.G', show_hidden_initial=True)
    PANRmag = forms.FloatField(required=False, label='PANSTAR.R', show_hidden_initial=True)
    PANImag = forms.FloatField(required=False, label='PANSTAR.I', show_hidden_initial=True)
    PANZmag = forms.FloatField(required=False, label='PANSTAR.Z', show_hidden_initial=True)
    PANYmag = forms.FloatField(required=False, label='PANSTAR.Y', show_hidden_initial=True)
    PANGmagerr = forms.FloatField(required=False, label='PANSTAR.Gerr', show_hidden_initial=True)
    PANRmagerr = forms.FloatField(required=False, label='PANSTAR.Rerr', show_hidden_initial=True)
    PANImagerr = forms.FloatField(required=False, label='PANSTAR.Ierr', show_hidden_initial=True)
    PANZmagerr = forms.FloatField(required=False, label='PANSTAR.Zerr', show_hidden_initial=True)
    PANYmagerr = forms.FloatField(required=False, label='PANSTAR.Yerr', show_hidden_initial=True)


# ===========================================================================================
#   SYSTEM PARAMETERS
# ===========================================================================================

class UpdateParamsForm(forms.Form):
    def __init__(self, params, *args, **kwargs):
        super(UpdateParamsForm, self).__init__(*args, **kwargs)
        for param in params:
            for paramset in param["params"]:
                index = param["params"].index(paramset)
                name = paramset["pinfo"].name
                self.fields[name + str(index)] = forms.FloatField(required=False, label=name + str(index),
                                                                  show_hidden_initial=True)
                self.fields[name + str(index) + "_err"] = forms.FloatField(required=False,
                                                                           label=name + str(index) + "_err",
                                                                           show_hidden_initial=True)

    def get_fields(self):
        None
#       for field_name in self.fields:


#        yield self[field_name]
