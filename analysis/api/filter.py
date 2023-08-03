from django_filters import rest_framework as filters

from AOTS.custom_permissions import get_allowed_objects_to_view_for_user
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

    @property
    def qs(self):
        parent = super(DataSetFilter, self).qs

        parent = get_allowed_objects_to_view_for_user(
            parent,
            self.request.user,
        )

        # get the column order from the GET dictionary
        getter = self.request.query_params.get
        if not getter('order[0][column]') is None:
            order_column = int(getter('order[0][column]'))
            order_name = getter('columns[%i][data]' % order_column)
            if getter('order[0][dir]') == 'desc': order_name = '-' + order_name

            return parent.order_by(order_name)
        else:
            return parent.order_by('name')


# ===============================================================
# Methods
# ===============================================================

class MethodFilter(filters.FilterSet):
    class Meta:
        model = Method
        fields = ['project', ]

    @property
    def qs(self):
        parent = super(MethodFilter, self).qs
        return get_allowed_objects_to_view_for_user(
            parent,
            self.request.user,
        )


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

    @property
    def qs(self):
        parent = super(ParameterFilter, self).qs

        return get_allowed_objects_to_view_for_user(
            parent,
            self.request.user,
            parameter_switch=True,
        )
