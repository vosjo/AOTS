
from django_filters import rest_framework as filters
from django.db.models import Count

from AOTS.custom_permissions import get_allowed_objects_to_view_for_user

from astropy.coordinates import Angle
from astroquery.simbad import Simbad

from stars.models import Star, Tag

# ===============================================================
# STARS
# ===============================================================

class StarFilter(filters.FilterSet):
    '''
    Filter definitions for table with stars
        - the filter order matters -> Gmag filter needs to come last,
          because it breaks other filter for some reason
    '''
    #   Name filter
    name = filters.CharFilter(
        field_name="name",
        method='filter_name',
        lookup_expr='icontains',
        )
    #name = filters.CharFilter(
        #field_name='name',
        #method='filter_identifier',
        #lookup_expr='icontains',
        #)
    #name2 = filters.CharFilter(
        #field_name="name",
        #lookup_expr='icontains',
        #)

    #   Coordinates filter
    coordinates = filters.CharFilter(
        field_name="ra",
        method='filter_coordinates',
        lookup_expr='icontains',
        )

    #   RA & DEC filter
    ra = filters.RangeFilter(field_name="ra",)
    dec = filters.RangeFilter(field_name="dec",)

    #   Classification filters
    classification = filters.CharFilter(
        field_name="classification",
        lookup_expr='icontains',
        )
    classification_type = filters.MultipleChoiceFilter(
        field_name="classification_type",
        choices=Star.CLASSIFICATION_TYPE_CHOICES,
        )

    #   Status filter
    status = filters.MultipleChoiceFilter(
        field_name="observing_status",
        choices=Star.OBSERVING_STATUS_CHOICES,
        )

    #   Tag filter
    tags = filters.ModelMultipleChoiceFilter(queryset=Tag.objects.all())

    #   Filter for # of photometry measurements, spectra, light curves
    nphot_min = filters.NumberFilter(
        field_name="photometry",
        method='filter_obs_gt',
        lookup_expr='gte',
        )
    nphot_max = filters.NumberFilter(
        field_name="photometry",
        method='filter_obs_lt',
        lookup_expr='lte',
        )

    nspec_min = filters.NumberFilter(
        field_name="spectrum",
        method='filter_obs_gt',
        lookup_expr='gte',
        )
    nspec_max = filters.NumberFilter(
        field_name="spectrum",
        method='filter_obs_lt',
        lookup_expr='lte',
        )

    nlc_min = filters.NumberFilter(
        field_name="lightcurve",
        method='filter_obs_gt',
        lookup_expr='gte',
        )
    nlc_max = filters.NumberFilter(
        field_name="lightcurve",
        method='filter_obs_lt',
        lookup_expr='lte',
        )

    #   Filter for G magnitudes
    mag_min = filters.NumberFilter(
        field_name="Gmag",
        method='filter_magnitude_gt',
        lookup_expr='gte',
        )
    mag_max = filters.NumberFilter(
        field_name="Gmag",
        method='filter_magnitude_lt',
        lookup_expr='lte',
        )

    #   Method definitions for the filter definitions above
    def filter_name(self, queryset, name, value):
        try:
            data = Simbad.query_object(value)
            ra = Angle(data['RA'][0], unit='hour').degree
            dec = Angle(data['DEC'][0], unit='degree').degree
            return queryset.filter(ra__range=[ra-15./3600., ra+15./3600.]).\
                filter(dec__range=[dec-5./3600., dec+5./3600.])
        except Exception:
            return queryset.filter(name__icontains=value)

    def filter_coordinates(self, queryset, name, value):
        ra, dec = value.split()

        if ':' in ra:
            ra = Angle(ra, unit='hour').degree
        else:
            ra = Angle(ra, unit='degree').degree

        dec = Angle(dec, unit='degree').degree

        return queryset.filter(ra__range=[ra-15./3600., ra+15./3600.]).filter(dec__range=[dec-5./3600., dec+5./3600.])


    def filter_magnitude_gt(self, queryset, name, value):
        return queryset.filter(
            photometry__band="GAIA2.G",
            photometry__measurement__gte=value,
            )

    def filter_magnitude_lt(self, queryset, name, value):
        return queryset.filter(
            photometry__band="GAIA2.G",
            photometry__measurement__lte=value,
            )

    #def filter_identifier(self, queryset, name, value):
        #return queryset.filter(identifier__name__icontains=value)

    #   General method for the observations filter
    #   - distinct=True is required to allow filter chains,
    #     false results will be returned otherwise
    def filter_obs_gt(self, queryset, name, value):
        return queryset.annotate(num_obs=Count(name, distinct=True)).\
            filter(num_obs__gte=value)

    def filter_obs_lt(self, queryset, name, value):
        return queryset.annotate(num_obs=Count(name, distinct=True)).\
            filter(num_obs__lte=value)

    class Meta:
        model    = Star
        fields   = ['project']

    @property
    def qs(self):
        parent = super().qs

        parent = get_allowed_objects_to_view_for_user(parent, self.request.user)

        #   Get the column order from the GET dictionary
        getter = self.request.query_params.get
        if not getter('order[0][column]') is None:
            order_column = int(getter('order[0][column]'))
            order_name = getter('columns[%i][data]' % order_column)
            if getter('order[0][dir]') == 'desc': order_name = '-'+order_name

            return parent.order_by(order_name)
        else:
            return parent.order_by('name')


# ===============================================================
# TAGS
# ===============================================================

class TagFilter(filters.FilterSet):

   class Meta:
      model = Tag
      fields = ['project',]

   @property
   def qs(self):
      parent = super().qs

      return get_allowed_objects_to_view_for_user(parent, self.request.user)

