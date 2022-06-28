from django_filters import rest_framework as filters

from AOTS.custom_permissions import get_allowed_objects_to_view_for_user
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
    target = filters.CharFilter(field_name="target", method="star_name_icontains", lookup_expr='icontains')

    hjd_min = filters.NumberFilter(field_name="hjd", lookup_expr='gte')
    hjd_max = filters.NumberFilter(field_name="hjd", lookup_expr='lte')

    exptime_min = filters.NumberFilter(field_name="exptime", lookup_expr='gte')
    exptime_max = filters.NumberFilter(field_name="exptime", lookup_expr='lte')

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
        fields = ['project', ]

    @property
    def qs(self):
        parent = super(SpectrumFilter, self).qs

        parent = get_allowed_objects_to_view_for_user(parent, self.request.user)

        # get the column order from the GET dictionary
        getter = self.request.query_params.get
        if not getter('order[0][column]') is None:
            order_column = int(getter('order[0][column]'))
            order_name = getter('columns[%i][data]' % order_column)
            if getter('order[0][dir]') == 'desc': order_name = '-' + order_name

            return parent.order_by(order_name)
        else:
            return parent


class UserInfoFilter(filters.FilterSet):
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
        return queryset.filter(spectrum_star__name__icontains=value)

    class Meta:
        model = UserInfo
        fields = ['project', ]

    @property
    def qs(self):
        parent = super(UserInfoFilter, self).qs

        parent = get_allowed_objects_to_view_for_user(parent, self.request.user)

        # get the column order from the GET dictionary
        getter = self.request.query_params.get
        if not getter('order[0][column]') is None:
            order_column = int(getter('order[0][column]'))
            order_name = getter('columns[%i][data]' % order_column)
            if getter('order[0][dir]') == 'desc': order_name = '-' + order_name

            return parent.order_by(order_name)
        else:
            return parent


# ===============================================================
#   SpecFile
# ===============================================================

class SpecFileFilter(filters.FilterSet):
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
        fields = ['project', ]

    @property
    def qs(self):
        parent = super(SpecFileFilter, self).qs

        parent = get_allowed_objects_to_view_for_user(parent, self.request.user)

        # get the column order from the GET dictionary
        getter = self.request.query_params.get
        if not getter('order[0][column]') is None:
            order_column = int(getter('order[0][column]'))
            order_name = getter('columns[%i][data]' % order_column)
            if getter('order[0][dir]') == 'desc': order_name = '-' + order_name

            return parent.order_by(order_name)
        else:
            return parent


# ===============================================================
#   RawSpecFile
# ===============================================================

class RawSpecFileFilter(filters.FilterSet):
    #   System filter
    systems = filters.CharFilter(
        field_name="stars",
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
        return queryset.filter(specfile__spectrum__star__name__icontains=value)

    #   File name method
    def file_name_regex(self, queryset, name, value):
        return queryset.filter(rawfile__regex='raw_spectra/.*' + value + '.*')

    class Meta:
        model = RawSpecFile
        fields = ['project', ]

    @property
    def qs(self):
        parent = super(RawSpecFileFilter, self).qs

        parent = get_allowed_objects_to_view_for_user(parent, self.request.user)

        # get the column order from the GET dictionary
        getter = self.request.query_params.get
        if not getter('order[0][column]') is None:
            order_column = int(getter('order[0][column]'))
            order_name = getter('columns[%i][data]' % order_column)
            if getter('order[0][dir]') == 'desc': order_name = '-' + order_name

            return parent.order_by(order_name)
        else:
            return parent


# ===============================================================
#   LightCurve
# ===============================================================

class LightCurveFilter(filters.FilterSet):
    target = filters.CharFilter(field_name="target", method="star_name_icontains", lookup_expr='icontains')

    hjd_min = filters.NumberFilter(field_name="hjd", lookup_expr='gte')
    hjd_max = filters.NumberFilter(field_name="hjd", lookup_expr='lte')

    instrument = filters.CharFilter(field_name="instrument", lookup_expr='icontains')

    pk = filters.Filter(field_name="pk", method="star_pk_in")

    def star_pk_in(self, queryset, name, value):
        pks = value.split(",")
        return queryset.filter(star__pk__in=pks)

    def star_name_icontains(self, queryset, name, value):
        return queryset.filter(spectrum__star__name__icontains=value)

    class Meta:
        model = LightCurve
        fields = ['project', ]

    @property
    def qs(self):
        parent = super(LightCurveFilter, self).qs

        parent = get_allowed_objects_to_view_for_user(parent, self.request.user)

        # get the column order from the GET dictionary
        getter = self.request.query_params.get
        if not getter('order[0][column]') is None:
            order_column = int(getter('order[0][column]'))
            order_name = getter('columns[%i][data]' % order_column)
            if getter('order[0][dir]') == 'desc': order_name = '-' + order_name

            return parent.order_by(order_name)
        else:
            return parent


# ===============================================================
#   Observatory
# ===============================================================

class ObservatoryFilter(filters.FilterSet):
    name = filters.CharFilter(field_name="name", lookup_expr='icontains')

    class Meta:
        model = Observatory
        fields = ['latitude', 'longitude', 'altitude', 'project']

    @property
    def qs(self):
        parent = super(ObservatoryFilter, self).qs

        return get_allowed_objects_to_view_for_user(parent, self.request.user)
