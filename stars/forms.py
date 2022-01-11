import re

from django import forms
from django.db.models import Q
from django.core.exceptions import ValidationError

from .models import Star, Identifier, Tag

from astropy.coordinates.angles import Angle


class RAField(forms.CharField):
    """
        Custom field to input Right Ascention (RA) in hexadecimal form in hours.
    """

    errormessage = 'Cannot interpret RA angle, try format: hh:mm:ss.ss, hh mm ss.ss or dd.ddddd'

    def clean(self, value):
        if not value:
            #return 0.0
            return None
        value = value.strip()

        #   Check if a decimal or hexadecimal number was given
        if re.match('^\d+\.\d+$', value):
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
            #return 0.0
            return None

        value = value.strip()

        #   Check if a decimal or hexadecimal number was given
        if re.match('^\d+\.\d+$', value):
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
    #   Target
    main_id = forms.CharField(max_length=50, required=True)
    ra = forms.CharField(max_length=15, required=True)
    dec = forms.CharField(max_length=15, required=True)
    # ra      = forms.FloatField(required=True)
    # dec     = forms.FloatField(required=True)

    #   Spectral type
    sp_type = forms.CharField(max_length=30, required=False)

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

    taglist = []
    ALLTAGS = Tag.objects.all()
    for tag in ALLTAGS:
        taglist.append((tag.pk, tag.name))

    tags = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,
                                     choices=taglist, required=False)

    INSTRUMENTS = (
        ('JHKWISE', 'JHK and WISE'),
        ('SKYMAP', 'SKYMAP'),
        ('APASS', 'APASS'),
        ('SDSS', 'SDSS'),
        ('PANSTAR', 'PANSTAR'),
    )

    instrument = forms.CharField(widget=forms.Select(choices=INSTRUMENTS))
