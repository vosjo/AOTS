from django_filters import rest_framework as filters

from AOTS.custom_permissions import get_allowed_objects_to_view_for_user
from analysis.models import Method, DataSet, Parameter
from analysis.models.SEDs import SED
from analysis.models.rvcurves import RVcurve
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

    class Meta:
        model = Parameter
        fields = ['star', ]

    @property
    def qs(self):
        parent = super(ParameterFilter, self).qs

        parent = get_allowed_objects_to_view_for_user(
            parent,
            self.request.user,
        )


# RVcurve and SED stuff


class SEDFilter(filters.FilterSet):
    target = filters.CharFilter(field_name="target", method="star_name_icontains", lookup_expr='icontains')

    pk = filters.Filter(field_name="pk", method="star_pk_in")

    def star_pk_in(self, queryset, name, value):
        pks = value.split(",")
        return queryset.filter(star__pk__in=pks)

    def star_name_icontains(self, queryset, name, value):
        return queryset.filter(star__name__icontains=value)

    class Meta:
        model = SED
        fields = ['project', ]

    @property
    def qs(self):
        parent = super(SEDFilter, self).qs

        parent = get_allowed_objects_to_view_for_user(parent, self.request.user)

        # get the column order from the GET dictionary (whatever that means)
        getter = self.request.query_params.get
        if not getter('order[0][column]') is None:
            order_column = int(getter('order[0][column]'))
            order_name = getter('columns[%i][data]' % order_column)
            if getter('order[0][dir]') == 'desc': order_name = '-' + order_name

            return parent.order_by(order_name)
        else:
            return parent.order_by('pk')


class RVcurveFilter(filters.FilterSet):
    target = filters.CharFilter(field_name="target", method="star_name_icontains", lookup_expr='icontains')

    logp = filters.CharFilter(field_name="logp", lookup_expr='icontains')

    pk = filters.Filter(field_name="pk", method="star_pk_in")

    def star_pk_in(self, queryset, name, value):
        pks = value.split(",")
        return queryset.filter(star__pk__in=pks)

    def star_name_icontains(self, queryset, name, value):
        return queryset.filter(star__name__icontains=value)

    class Meta:
        model = RVcurve
        fields = ['project', ]

    @property
    def qs(self):
        parent = super(RVcurveFilter, self).qs

        parent = get_allowed_objects_to_view_for_user(parent, self.request.user)

        # get the column order from the GET dictionary
        getter = self.request.query_params.get
        if not getter('order[0][column]') is None:
            order_column = int(getter('order[0][column]'))
            order_name = getter('columns[%i][data]' % order_column)
            if getter('order[0][dir]') == 'desc': order_name = '-' + order_name

            return parent.order_by(order_name)
        else:
            return parent.order_by('pk')
