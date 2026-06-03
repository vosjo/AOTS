from django_filters import rest_framework as filters

from analysis.models import Method, DataSet, Parameter
from stars.models import Project


# ===============================================================
# DataSet
# ===============================================================

class DataSetFilter(filters.FilterSet):
    system = filters.CharFilter(
        field_name="star",
        method="star_name_icontains",
        lookup_expr='icontains',
    )

    name = filters.CharFilter(field_name="name", lookup_expr='icontains')

    method = filters.CharFilter(
        field_name="method",
        method="method_name_icontains",
        lookup_expr='icontains',
    )

    def star_name_icontains(self, queryset, name, value):
        return queryset.filter(star__name__icontains=value)

    def method_name_icontains(self, queryset, name, value):
        return queryset.filter(method__name__icontains=value)

    class Meta:
        model = DataSet
        fields = ['project', ]


# ===============================================================
# Methods
# ===============================================================

class MethodFilter(filters.FilterSet):
    class Meta:
        model = Method
        fields = ['project', ]


# ===============================================================
# Parameter
# ===============================================================

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
