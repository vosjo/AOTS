from django_filters import rest_framework as filters

from analysis.categories import CATEGORY_META, DatasetCategory
from analysis.models import DataSet, Parameter
from stars.models import Project


class DataSetFilter(filters.FilterSet):
    system = filters.CharFilter(
        field_name="star",
        method="star_name_icontains",
        lookup_expr='icontains',
    )

    name = filters.CharFilter(field_name="name", lookup_expr='icontains')

    category = filters.CharFilter(method='category_filter')

    def star_name_icontains(self, queryset, name, value):
        return queryset.filter(star__name__icontains=value)

    def category_filter(self, queryset, name, value):
        if not value:
            return queryset
        needle = value.strip().lower()
        codes = [
            code for code, meta in CATEGORY_META.items()
            if needle in code.lower() or needle in meta.label.lower()
        ]
        if codes:
            return queryset.filter(category__in=codes)
        return queryset.filter(category=DatasetCategory.UNKNOWN)

    class Meta:
        model = DataSet
        fields = ['project', ]


class ParameterFilter(filters.FilterSet):
    project = filters.ModelChoiceFilter(
        queryset=Project.objects.all(),
        field_name="star__project",
        lookup_expr='exact',
    )

    star_pk = filters.NumberFilter(
        field_name="star",
        lookup_expr='exact',
        method="star_pk_exact",
    )

    def star_pk_exact(self, queryset, name, value):
        return queryset.filter(star__pk__exact=value)

    class Meta:
        model = Parameter
        fields = ['star', ]
