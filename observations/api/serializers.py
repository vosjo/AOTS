from astropy.time import Time
from django.urls import reverse
from rest_framework.serializers import ModelSerializer, SerializerMethodField

from observations.models import (
    Spectrum,
    UserInfo,
    SpecFile,
    RawSpecFile,
    LightCurve,
    Observatory,
)
from stars.api.serializers import SimpleStarSerializer
from .formatting import (
    dgr2dms,
    dgr2hms,
    format_float_negative_na,
    format_wind,
    hjd2date,
    hjd2datetime,
)


# ===============================================================
# SPECTRA
# ===============================================================

class SpectrumListSerializer(ModelSerializer):
    star = SerializerMethodField()
    specfiles = SerializerMethodField()
    href = SerializerMethodField()
    has_raw_files = SerializerMethodField()

    class Meta:
        model = Spectrum
        fields = [
            'pk',
            'star',
            'project',
            'hjd',
            'exptime',
            'instrument',
            'telescope',
            'valid',
            'fluxcal',
            'specfiles',
            'has_raw_files',
            'href',
            'airmass',
            'resolution',
        ]
        datatables_always_serialize = (
            'pk', 'specfiles', 'has_raw_files', 'telescope', 'href',
        )
        read_only_fields = ('pk',)

    def get_star(self, obj):
        if obj.star is None:
            return ''
        else:
            return SimpleStarSerializer(obj.star).data

    def get_specfiles(self, obj):
        specfiles = SimpleSpecFileSerializer(obj.specfile_set, many=True).data
        return specfiles

    def get_has_raw_files(self, obj):
        for specfile in obj.specfile_set.all():
            if specfile.rawspecfile_set.all():
                return True
        return False

    def get_href(self, obj):
        return reverse('observations:spectrum_detail', kwargs={'project': obj.project.slug, 'spectrum_id': obj.pk})


class SpectrumSerializer(ModelSerializer):
    star = SerializerMethodField()
    observatory = SerializerMethodField()
    specfiles = SerializerMethodField()
    href = SerializerMethodField()

    class Meta:
        model = Spectrum
        fields = [
            'pk',
            'star',
            'project',
            'hjd',
            'ra',
            'dec',
            'exptime',
            'instrument',
            'telescope',
            'observatory',
            'valid',
            'fluxcal',
            'flux_units',
            'note',
            'specfiles',
            'href',
            'airmass',
            'resolution',
        ]
        read_only_fields = ('pk',)

    def get_star(self, obj):
        if obj.star is None:
            return ''
        else:
            return SimpleStarSerializer(obj.star).data
        # return Star.objects.get(pk=obj.star).name

    def get_observatory(self, obj):
        try:
            return obj.observatory.name
        except:
            return ''

    def get_specfiles(self, obj):
        specfiles = SimpleSpecFileSerializer(obj.specfile_set, many=True).data
        return specfiles

    def get_href(self, obj):
        return reverse('observations:spectrum_detail', kwargs={'project': obj.project.slug, 'spectrum_id': obj.pk})


class SpectrumSpecFileDetailSerializer(ModelSerializer):
    download_url = SerializerMethodField()
    header_url = SerializerMethodField()

    class Meta:
        model = SpecFile
        fields = [
            'pk',
            'filetype',
            'hjd',
            'instrument',
            'download_url',
            'header_url',
        ]
        read_only_fields = fields

    def get_download_url(self, obj):
        if obj.specfile:
            return obj.specfile.url
        return ''

    def get_header_url(self, obj):
        return reverse('observations-api:specfile_header', kwargs={'specfile_pk': obj.pk})


class SpectrumDetailSerializer(SpectrumSerializer):
    title = SerializerMethodField()
    target_coords = SerializerMethodField()
    obs_coords = SerializerMethodField()
    hjd_date = SerializerMethodField()
    hjd_datetime = SerializerMethodField()
    snr_display = SerializerMethodField()
    seeing_display = SerializerMethodField()
    airmass_display = SerializerMethodField()
    exptime_display = SerializerMethodField()
    resolution_display = SerializerMethodField()
    moon_illumination_display = SerializerMethodField()
    moon_separation_display = SerializerMethodField()
    wind_display = SerializerMethodField()
    weather_url = SerializerMethodField()
    observatory_short_name = SerializerMethodField()
    default_rebin = SerializerMethodField()
    related_spectra = SerializerMethodField()

    class Meta(SpectrumSerializer.Meta):
        fields = SpectrumSerializer.Meta.fields + [
            'title',
            'objectname',
            'observer',
            'target_coords',
            'obs_coords',
            'hjd_date',
            'hjd_datetime',
            'snr_display',
            'seeing_display',
            'airmass_display',
            'exptime_display',
            'resolution_display',
            'moon_illumination_display',
            'moon_separation_display',
            'wind_display',
            'weather_url',
            'observatory_short_name',
            'normalized',
            'decomposed',
            'master',
            'barycor',
            'barycor_bool',
            'default_rebin',
            'related_spectra',
        ]
        read_only_fields = SpectrumSerializer.Meta.read_only_fields + (
            'title',
            'objectname',
            'observer',
            'target_coords',
            'obs_coords',
            'hjd_date',
            'hjd_datetime',
            'snr_display',
            'seeing_display',
            'airmass_display',
            'exptime_display',
            'resolution_display',
            'moon_illumination_display',
            'moon_separation_display',
            'wind_display',
            'weather_url',
            'observatory_short_name',
            'normalized',
            'decomposed',
            'master',
            'barycor',
            'barycor_bool',
            'default_rebin',
            'related_spectra',
            'star',
            'specfiles',
            'href',
            'observatory',
            'hjd',
            'ra',
            'dec',
            'exptime',
            'instrument',
            'telescope',
            'airmass',
            'resolution',
            'project',
        )

    def get_title(self, obj):
        return str(obj)

    def get_target_coords(self, obj):
        if obj.star is None:
            return ''
        return f'{dgr2hms(obj.star.ra)} {dgr2dms(obj.star.dec)}'

    def get_obs_coords(self, obj):
        return f'{dgr2hms(obj.ra)} {dgr2dms(obj.dec)}'

    def get_hjd_date(self, obj):
        return hjd2date(obj.hjd)

    def get_hjd_datetime(self, obj):
        return hjd2datetime(obj.hjd)

    def get_snr_display(self, obj):
        return format_float_negative_na(obj.snr, decimals=0)

    def get_seeing_display(self, obj):
        return format_float_negative_na(obj.seeing, decimals=1, unit='"')

    def get_airmass_display(self, obj):
        return format_float_negative_na(obj.airmass, decimals=2)

    def get_exptime_display(self, obj):
        return format_float_negative_na(obj.exptime, decimals=1, unit='s')

    def get_resolution_display(self, obj):
        return format_float_negative_na(obj.resolution, decimals=0)

    def get_moon_illumination_display(self, obj):
        return format_float_negative_na(obj.moon_illumination, decimals=1, unit='%')

    def get_moon_separation_display(self, obj):
        return format_float_negative_na(obj.moon_separation, decimals=1, unit='°')

    def get_wind_display(self, obj):
        return format_wind(obj.wind_speed, obj.wind_direction)

    def get_weather_url(self, obj):
        return obj.get_weather_url()

    def get_observatory_short_name(self, obj):
        if obj.observatory is None:
            return ''
        return obj.observatory.short_name

    def get_default_rebin(self, obj):
        total_size = sum(
            sf.specfile.size for sf in obj.specfile_set.all() if sf.specfile
        )
        return 10 if total_size > 500000 else 1

    def get_related_spectra(self, obj):
        if obj.star_id is None:
            return []
        grouped = []
        instruments = (
            obj.star.spectrum_set.values_list('instrument', flat=True).distinct()
        )
        for inst in sorted(set(instruments)):
            spectra = obj.star.spectrum_set.filter(instrument=inst).order_by('hjd')
            grouped.append({
                'instrument': inst,
                'spectra': [
                    {
                        'pk': spec.pk,
                        'hjd': spec.hjd,
                        'hjd_date': hjd2date(spec.hjd),
                        'is_current': spec.pk == obj.pk,
                    }
                    for spec in spectra
                ],
            })
        return grouped

    def get_specfiles(self, obj):
        return SpectrumSpecFileDetailSerializer(obj.specfile_set.all(), many=True).data


class UserInfoSerializer(ModelSerializer):
    spectrum = SerializerMethodField()
    observatory = SerializerMethodField()

    class Meta:
        model = UserInfo
        exclude = ['added_on', 'last_modified', 'added_by']
        read_only_fields = ('pk',)

    def get_spectrum(self, obj):
        if obj.spectrum is None:
            return ''
        return reverse(
            'observations:spectrum_detail',
            kwargs={'project': obj.project.slug, 'spectrum_id': obj.spectrum.pk},
        )

    def get_observatory(self, obj):
        try:
            return obj.observatory.name
        except:
            return ''


# ===============================================================
# SPECFILE
# ===============================================================

class SpecFileListSerializer(ModelSerializer):
    star = SerializerMethodField()
    spectrum = SerializerMethodField()
    spectrum_info = SerializerMethodField()
    rawspecfiles = SerializerMethodField()
    added_on = SerializerMethodField()
    filename = SerializerMethodField()

    class Meta:
        model = SpecFile
        fields = [
            'pk',
            'star',
            'spectrum',
            'spectrum_info',
            'rawspecfiles',
            'hjd',
            'instrument',
            'filetype',
            'added_on',
            'filename',
            'project',
        ]
        read_only_fields = ('pk',)

    def get_star(self, obj):
        if obj.spectrum is None or obj.spectrum.star is None:
            return ''
        link = reverse(
            'systems:star_detail',
            kwargs={'project': obj.project.slug, 'star_id': obj.spectrum.star.pk},
        )
        return {obj.spectrum.star.name: link}

    def get_spectrum(self, obj):
        if obj.spectrum is None:
            return ''
        return reverse(
            'observations:spectrum_detail',
            kwargs={'project': obj.project.slug, 'spectrum_id': obj.spectrum.pk},
        )

    def get_spectrum_info(self, obj):
        if obj.spectrum is None:
            return None
        spectrum = obj.spectrum
        target = ''
        if spectrum.star is not None:
            target = spectrum.star.name
        elif spectrum.objectname:
            target = spectrum.objectname
        return {
            'pk': spectrum.pk,
            'hjd': spectrum.hjd,
            'target': target,
            'instrument': spectrum.instrument,
        }

    def get_rawspecfiles(self, obj):
        return list(obj.rawspecfile_set.values_list('pk', flat=True))

    def get_added_on(self, obj):
        return Time(obj.history.earliest().history_date, precision=0).iso

    def get_filename(self, obj):
        return obj.specfile.name.split('/')[-1]


class SpecFileSerializer(ModelSerializer):
    star = SerializerMethodField()
    star_pk = SerializerMethodField()
    spectrum = SerializerMethodField()
    added_on = SerializerMethodField()
    filename = SerializerMethodField()

    class Meta:
        model = SpecFile
        fields = [
            'pk',
            'star',
            'star_pk',
            'spectrum',
            'hjd',
            'instrument',
            'filetype',
            'added_on',
            'exptime',
            'resolution',
            'filename',
            'specfile',
            'project',
        ]
        read_only_fields = ('pk', 'star', 'star_pk')

    def get_star(self, obj):
        if obj.spectrum is None or obj.spectrum.star is None:
            return ''
        link = reverse(
            'systems:star_detail',
            kwargs={'project': obj.project.slug, 'star_id': obj.spectrum.star.pk},
        )
        return {obj.spectrum.star.name: link}

    def get_star_pk(self, obj):
        if obj.spectrum is None or obj.spectrum.star is None:
            return {None: None}
        return {obj.spectrum.star.pk: obj.spectrum.star.name}

    def get_spectrum(self, obj):
        if obj.spectrum is None:
            return ''
        return reverse(
            'observations:spectrum_detail',
            kwargs={'project': obj.project.slug, 'spectrum_id': obj.spectrum.pk},
        )

    def get_added_on(self, obj):
        return Time(obj.history.earliest().history_date, precision=0).iso

    def get_filename(self, obj):
        return obj.specfile.name.split('/')[-1]


class SimpleSpecFileSerializer(ModelSerializer):
    class Meta:
        model = SpecFile
        fields = [
            'pk',
            'hjd',
            'instrument',
            'filetype',
        ]
        read_only_fields = ('pk',)


# ===============================================================
# RAWSPECFILE
# ===============================================================

class RawSpecFileSerializer(ModelSerializer):
    systems = SerializerMethodField()
    spectra = SerializerMethodField()
    added_on = SerializerMethodField()
    filename = SerializerMethodField()
    added_by = SerializerMethodField()

    class Meta:
        model = RawSpecFile
        fields = [
            'pk',
            'specfile',
            'star',
            'systems',
            'spectra',
            'hjd',
            'obs_date',
            'instrument',
            'filetype',
            'added_on',
            'filename',
            'exptime',
            'added_by',
        ]
        read_only_fields = ('pk', 'systems',)

    def get_systems(self, obj):
        SystemDict = {}

        #   Process specfile allocations
        for sfile in obj.specfile.all():
            if sfile.spectrum is not None and sfile.spectrum.star is not None:
                SystemDict[sfile.spectrum.star.name] = reverse(
                    'systems:star_detail',
                    kwargs={
                        'project': sfile.project.slug,
                        'star_id': sfile.spectrum.star.pk,
                    },
                )

        #   Process star allocations
        for star in obj.star.all():
            SystemDict[star.name] = reverse(
                'systems:star_detail',
                kwargs={
                    'project': star.project.slug,
                    'star_id': star.pk,
                },
            )

        return SystemDict

    def get_spectra(self, obj):
        spectrum_pks = set()
        for sfile in obj.specfile.all():
            if sfile.spectrum_id is not None:
                spectrum_pks.add(sfile.spectrum_id)
        return sorted(spectrum_pks)

    def get_added_on(self, obj):
        return Time(obj.history.earliest().history_date, precision=0).iso

    def get_filename(self, obj):
        return obj.rawfile.name.split('/')[-1]

    def get_added_by(self, obj):
        if obj.history.earliest().history_user is None:
            return '-'

        return obj.history.earliest().history_user.username


# ===============================================================
# Licht Curves
# ===============================================================

class LightCurveSerializer(ModelSerializer):
    star = SerializerMethodField()
    href = SerializerMethodField()

    class Meta:
        model = LightCurve
        fields = [
            'pk',
            'star',
            'project',
            'hjd',
            'exptime',
            'cadence',
            'instrument',
            'telescope',
            'valid',
            'note',
            'href',
        ]
        read_only_fields = ('pk',)
        datatables_always_serialize = ('pk', 'telescope', 'href')

    def get_star(self, obj):
        if obj.star is None:
            return ''
        else:
            return SimpleStarSerializer(obj.star).data

    def get_href(self, obj):
        return reverse('observations:lightcurve_detail', kwargs={'project': obj.project.slug, 'lightcurve_id': obj.pk})


class LightCurveDetailSerializer(LightCurveSerializer):
    title = SerializerMethodField()
    target_coords = SerializerMethodField()
    obs_coords = SerializerMethodField()
    hjd_date = SerializerMethodField()
    hjd_datetime = SerializerMethodField()
    exptime_display = SerializerMethodField()
    cadence_display = SerializerMethodField()
    duration_display = SerializerMethodField()
    seeing_display = SerializerMethodField()
    moon_illumination_display = SerializerMethodField()
    wind_display = SerializerMethodField()
    weather_url = SerializerMethodField()
    observatory_short_name = SerializerMethodField()
    download_url = SerializerMethodField()
    header_url = SerializerMethodField()
    related_lightcurves = SerializerMethodField()

    class Meta(LightCurveSerializer.Meta):
        fields = LightCurveSerializer.Meta.fields + [
            'title',
            'objectname',
            'passband',
            'observer',
            'ra',
            'dec',
            'duration',
            'seeing',
            'moon_illumination',
            'wind_speed',
            'wind_direction',
            'filetype',
            'target_coords',
            'obs_coords',
            'hjd_date',
            'hjd_datetime',
            'exptime_display',
            'cadence_display',
            'duration_display',
            'seeing_display',
            'moon_illumination_display',
            'wind_display',
            'weather_url',
            'observatory_short_name',
            'download_url',
            'header_url',
            'related_lightcurves',
        ]
        read_only_fields = LightCurveSerializer.Meta.read_only_fields + (
            'title',
            'objectname',
            'passband',
            'observer',
            'ra',
            'dec',
            'duration',
            'seeing',
            'moon_illumination',
            'wind_speed',
            'wind_direction',
            'filetype',
            'target_coords',
            'obs_coords',
            'hjd_date',
            'hjd_datetime',
            'exptime_display',
            'cadence_display',
            'duration_display',
            'seeing_display',
            'moon_illumination_display',
            'wind_display',
            'weather_url',
            'observatory_short_name',
            'download_url',
            'header_url',
            'related_lightcurves',
            'star',
            'href',
            'hjd',
            'cadence',
            'instrument',
            'telescope',
            'project',
        )
        datatables_always_serialize = ('pk', 'telescope', 'href')

    def get_title(self, obj):
        return str(obj)

    def get_target_coords(self, obj):
        if obj.star is None:
            return ''
        return f'{dgr2hms(obj.star.ra)} {dgr2dms(obj.star.dec)}'

    def get_obs_coords(self, obj):
        return f'{dgr2hms(obj.ra)} {dgr2dms(obj.dec)}'

    def get_hjd_date(self, obj):
        return hjd2date(obj.hjd)

    def get_hjd_datetime(self, obj):
        return hjd2datetime(obj.hjd)

    def get_exptime_display(self, obj):
        return format_float_negative_na(obj.exptime, decimals=1, unit='s')

    def get_cadence_display(self, obj):
        return format_float_negative_na(obj.cadence, decimals=1, unit='s')

    def get_duration_display(self, obj):
        return format_float_negative_na(obj.duration, decimals=2, unit='h')

    def get_seeing_display(self, obj):
        return format_float_negative_na(obj.seeing, decimals=1, unit='"')

    def get_moon_illumination_display(self, obj):
        return format_float_negative_na(obj.moon_illumination, decimals=1, unit='%')

    def get_wind_display(self, obj):
        return format_wind(obj.wind_speed, obj.wind_direction)

    def get_weather_url(self, obj):
        return obj.get_weather_url()

    def get_observatory_short_name(self, obj):
        if obj.observatory is None:
            return ''
        return obj.observatory.short_name

    def get_download_url(self, obj):
        if obj.lcfile:
            return obj.lcfile.url
        return ''

    def get_header_url(self, obj):
        return reverse('observations-api:lightcurve_header', kwargs={'lightcurve_pk': obj.pk})

    def get_related_lightcurves(self, obj):
        if obj.star_id is None:
            return []
        grouped = []
        instruments = obj.star.lightcurve_set.values_list('instrument', flat=True).distinct()
        for inst in sorted(set(instruments)):
            lightcurves = obj.star.lightcurve_set.filter(instrument=inst).order_by('hjd')
            grouped.append({
                'instrument': inst,
                'lightcurves': [
                    {
                        'pk': lc.pk,
                        'hjd': lc.hjd,
                        'hjd_date': hjd2date(lc.hjd),
                        'is_current': lc.pk == obj.pk,
                    }
                    for lc in lightcurves
                ],
            })
        return grouped


# ===============================================================
# Observatory
# ===============================================================

class ObservatorySerializer(ModelSerializer):
    class Meta:
        model = Observatory
        fields = [
            'pk',
            'project',
            'name',
            'short_name',
            'telescopes',
            'latitude',
            'longitude',
            'altitude',
            'space_craft',
            'note',
            'url',
            'weatherurl',
        ]
        read_only_fields = ('pk',)
