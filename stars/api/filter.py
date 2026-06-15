from astropy.coordinates import Angle
from astroquery.simbad import Simbad
from django.db.models import Count
from django_filters import rest_framework as filters

from AOTS.filter_scoping import project_id_from_mapping, project_pk_filter
from stars.models import Star, Tag


# ===============================================================
# STARS
# ===============================================================

class StarFilter(filters.FilterSet):
    """
    Filter definitions for table with stars
        - the filter order matters -> Gmag filter needs to come last,
          because it breaks other filter for some reason
    """
    project = project_pk_filter()

    #   Name filter
    name = filters.CharFilter(
        field_name="name",
        method='filter_name',
        lookup_expr='icontains',
    )
    # name = filters.CharFilter(
    # field_name='name',
    # method='filter_identifier',
    # lookup_expr='icontains',
    # )
    # name2 = filters.CharFilter(
    # field_name="name",
    # lookup_expr='icontains',
    # )

    #   Coordinates filter
    coordinates = filters.CharFilter(
        field_name="ra",
        method='filter_coordinates',
        lookup_expr='icontains',
    )

    #   RA & DEC filter
    # ra = filters.RangeFilter(field_name="ra", )
    # dec = filters.RangeFilter(field_name="dec", )
    ra = filters.CharFilter(
        field_name="ra",
        method='filter_ra',
        lookup_expr='icontains',
    )
    dec = filters.CharFilter(
        field_name="dec",
        method='filter_dec',
        lookup_expr='icontains',
    )

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
    tags = filters.CharFilter(method='filter_by_tags')

    def filter_by_tags(self, queryset, name, value):
        request_data = getattr(self, 'data', None)
        if request_data is None:
            return queryset
        if hasattr(request_data, 'getlist'):
            tag_ids = request_data.getlist('tags')
        else:
            raw = request_data.get('tags', [])
            tag_ids = raw if isinstance(raw, list) else [raw]
        try:
            tag_ids = [int(tag_id) for tag_id in tag_ids if str(tag_id).strip()]
        except (TypeError, ValueError):
            return queryset.none()
        if not tag_ids:
            return queryset
        project_id = project_id_from_mapping(request_data)
        tag_qs = Tag.objects.filter(pk__in=tag_ids)
        if project_id:
            tag_qs = tag_qs.filter(project_id=project_id)
        if not tag_qs.exists():
            return queryset.none()
        return queryset.filter(tags__in=tag_qs).distinct()

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
            return queryset.filter(ra__range=[ra - 15. / 3600., ra + 15. / 3600.]). \
                filter(dec__range=[dec - 5. / 3600., dec + 5. / 3600.])
        except Exception:
            return queryset.filter(name__icontains=value)

    def filter_coordinates(self, queryset, name, value):
        ra, dec = value.split('--')

        if ':' in ra:
            ra = Angle(ra, unit='hour').degree
        else:
            ra = Angle(ra, unit='degree').degree

        dec = Angle(dec, unit='degree').degree

        return queryset.filter(ra__range=[ra - 15. / 3600., ra + 15. / 3600.]).filter(
            dec__range=[dec - 5. / 3600., dec + 5. / 3600.])

    def filter_ra(self, queryset, name, value):
        ra_min, ra_max = value.split('--')

        try:
            if ':' in ra_min:
                ra_min = Angle(ra_min, unit='hour').degree
            else:
                ra_min = Angle(ra_min, unit='degree').degree
        except:
            ra_min = Angle(0., unit='degree').degree

        try:
            if ':' in ra_max:
                ra_max = Angle(ra_max, unit='hour').degree
            else:
                ra_max = Angle(ra_max, unit='degree').degree
        except:
            ra_max = Angle(360., unit='degree').degree

        return queryset.filter(ra__range=[ra_min, ra_max])

    def filter_dec(self, queryset, name, value):
        dec_min, dec_max = value.split('--')

        try:
            dec_min = float(dec_min)
        except:
            dec_min = -90.

        try:
            dec_max = float(dec_max)
        except:
            dec_max = 90.

        dec_min = Angle(dec_min, unit='degree').degree
        dec_max = Angle(dec_max, unit='degree').degree

        return queryset.filter(dec__range=[dec_min, dec_max])

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

    # def filter_identifier(self, queryset, name, value):
    # return queryset.filter(identifier__name__icontains=value)

    #   General method for the observations filter
    #   - distinct=True is required to allow filter chains,
    #     false results will be returned otherwise
    def filter_obs_gt(self, queryset, name, value):
        return queryset.annotate(num_obs=Count(name, distinct=True)). \
            filter(num_obs__gte=value)

    def filter_obs_lt(self, queryset, name, value):
        return queryset.annotate(num_obs=Count(name, distinct=True)). \
            filter(num_obs__lte=value)

    class Meta:
        model = Star
        fields = []


# ===============================================================
# TAGS
# ===============================================================

class TagFilter(filters.FilterSet):
    project = project_pk_filter()

    class Meta:
        model = Tag
        fields = []
