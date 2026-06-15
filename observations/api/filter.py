from django_filters import rest_framework as filters

from AOTS.filter_scoping import project_pk_filter
from observations.models import (
    Spectrum,
    UserInfo,
    SpecFile,
    RawSpecFile,
    LightCurve,
    Observatory,
)


# ===============================================================
#   Spectrum
# ===============================================================

class SpectrumFilter(filters.FilterSet):
    project = project_pk_filter()

    target = filters.CharFilter(field_name="target", method="star_name_icontains", lookup_expr='icontains')

    hjd_min = filters.NumberFilter(field_name="hjd", lookup_expr='gte')
    hjd_max = filters.NumberFilter(field_name="hjd", lookup_expr='lte')

    exptime_min = filters.NumberFilter(field_name="exptime", lookup_expr='gte')
    exptime_max = filters.NumberFilter(field_name="exptime", lookup_expr='lte')

    resolution_min = filters.NumberFilter(field_name="resolution", lookup_expr='gte')
    resolution_max = filters.NumberFilter(field_name="resolution", lookup_expr='lte')

    airmass_min = filters.NumberFilter(field_name="airmass", lookup_expr='gte')
    airmass_max = filters.NumberFilter(field_name="airmass", lookup_expr='lte')

    instrument = filters.CharFilter(field_name="instrument", lookup_expr='icontains')

    telescope = filters.CharFilter(field_name="telescope", lookup_expr='icontains')

    fluxcal = filters.BooleanFilter(field_name='fluxcal')

    pk = filters.Filter(field_name="pk", method="star_pk_in")

    def star_pk_in(self, queryset, name, value):
        pks = value.split(",")
        return queryset.filter(star__pk__in=pks)

    def star_name_icontains(self, queryset, name, value):
        return queryset.filter(star__name__icontains=value)

    class Meta:
        model = Spectrum
        fields = []


class UserInfoFilter(filters.FilterSet):
    project = project_pk_filter()

    target = filters.CharFilter(
        field_name="target",
        method="star_name_icontains",
        lookup_expr='icontains',
    )

    hjd_min = filters.NumberFilter(field_name="hjd", lookup_expr='gte')
    hjd_max = filters.NumberFilter(field_name="hjd", lookup_expr='lte')

    exptime_min = filters.NumberFilter(field_name="exptime", lookup_expr='gte')
    exptime_max = filters.NumberFilter(field_name="exptime", lookup_expr='lte')

    instrument = filters.CharFilter(
        field_name="instrument",
        lookup_expr='icontains',
    )

    telescope = filters.CharFilter(
        field_name="telescope",
        lookup_expr='icontains',
    )

    fluxcal = filters.BooleanFilter(field_name='fluxcal')

    def star_name_icontains(self, queryset, name, value):
        return queryset.filter(spectrum__star__name__icontains=value)

    class Meta:
        model = UserInfo
        fields = []


# ===============================================================
#   SpecFile
# ===============================================================

class SpecFileFilter(filters.FilterSet):
    project = project_pk_filter()

    #   Target filter
    target = filters.CharFilter(
        field_name="target",
        method="star_name_icontains",
        lookup_expr='icontains',
    )

    #   JD filter
    hjd_min = filters.NumberFilter(field_name="hjd", lookup_expr='gte')
    hjd_max = filters.NumberFilter(field_name="hjd", lookup_expr='lte')

    #   Instrument filter
    instrument = filters.CharFilter(
        field_name="instrument",
        lookup_expr='icontains',
    )

    #   File type filter
    filetype = filters.CharFilter(
        field_name="filetype",
        lookup_expr='icontains',
    )

    #   File name filter
    filename = filters.CharFilter(
        field_name="filename",
        method="file_name_regex",
        lookup_expr='icontains',
    )

    #   Target method
    def star_name_icontains(self, queryset, name, value):
        return queryset.filter(spectrum__star__name__icontains=value)

    #   File name methode
    def file_name_regex(self, queryset, name, value):
        return queryset.filter(specfile__regex='spectra/.*' + value + '.*')

    class Meta:
        model = SpecFile
        fields = []


# ===============================================================
#   RawSpecFile
# ===============================================================

class RawSpecFileFilter(filters.FilterSet):
    project = project_pk_filter()

    #   System filter
    systems = filters.CharFilter(
        field_name="star",
        method="system_name_icontains",
        lookup_expr='icontains',
    )

    #   JD filter
    hjd_min = filters.NumberFilter(field_name="hjd", lookup_expr='gte')
    hjd_max = filters.NumberFilter(field_name="hjd", lookup_expr='lte')

    #   Instrument filter
    instrument = filters.CharFilter(
        field_name="instrument",
        lookup_expr='icontains',
    )

    #   File type filter
    filetype = filters.CharFilter(
        field_name="filetype",
        lookup_expr='icontains',
    )

    #   Exposure time filter
    expo_min = filters.NumberFilter(field_name="exptime", lookup_expr='gte')
    expo_max = filters.NumberFilter(field_name="exptime", lookup_expr='lte')

    #   File name filter
    filename = filters.CharFilter(
        field_name="filename",
        method="file_name_regex",
        lookup_expr='icontains',
    )

    #   Obs. date filter
    obs_date = filters.CharFilter(
        field_name='obs_date',
        lookup_expr='icontains',
    )

    obs_date_min = filters.NumberFilter(field_name="hjd", lookup_expr='gte')
    obs_date_max = filters.NumberFilter(field_name="hjd", lookup_expr='lte')

    #   System method
    def system_name_icontains(self, queryset, name, value):
        return queryset.filter(star__name__icontains=value) \
            | queryset.filter(specfile__spectrum__star__name__icontains=value)

    #   File name method
    def file_name_regex(self, queryset, name, value):
        return queryset.filter(rawfile__regex='raw_spectra/.*' + value + '.*')

    class Meta:
        model = RawSpecFile
        fields = []


# ===============================================================
#   LightCurve
# ===============================================================

class LightCurveFilter(filters.FilterSet):
    project = project_pk_filter()

    target = filters.CharFilter(field_name="target", method="star_name_icontains", lookup_expr='icontains')

    hjd_min = filters.NumberFilter(field_name="hjd", lookup_expr='gte')
    hjd_max = filters.NumberFilter(field_name="hjd", lookup_expr='lte')

    exptime_min = filters.NumberFilter(field_name="exptime", lookup_expr='gte')
    exptime_max = filters.NumberFilter(field_name="exptime", lookup_expr='lte')

    instrument = filters.CharFilter(field_name="instrument", lookup_expr='icontains')

    telescope = filters.CharFilter(field_name="telescope", lookup_expr='icontains')

    pk = filters.Filter(field_name="pk", method="star_pk_in")

    def star_pk_in(self, queryset, name, value):
        pks = value.split(",")
        return queryset.filter(star__pk__in=pks)

    def star_name_icontains(self, queryset, name, value):
        return queryset.filter(star__name__icontains=value)

    class Meta:
        model = LightCurve
        fields = []


# ===============================================================
#   Observatory
# ===============================================================

class ObservatoryFilter(filters.FilterSet):
    project = project_pk_filter()

    name = filters.CharFilter(field_name="name", lookup_expr='icontains')

    class Meta:
        model = Observatory
        fields = ['latitude', 'longitude', 'altitude']
