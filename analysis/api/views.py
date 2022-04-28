from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from AOTS.custom_permissions import get_allowed_objects_to_view_for_user
from analysis.auxil import process_datasets
from analysis.models import Method, DataSet, Parameter
from stars.models import Project
from .serializers import MethodSerializer, DataSetListSerializer, ParameterListSerializer


# ===============================================================
# DataSet
# ===============================================================

class DataSetFilter(filters.FilterSet):
    class Meta:
        model = DataSet
        fields = ['project', ]

    @property
    def qs(self):
        parent = super(DataSetFilter, self).qs

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


class DatasetViewSet(viewsets.ModelViewSet):
    queryset = DataSet.objects.all()
    serializer_class = DataSetListSerializer

    filter_backends = (DjangoFilterBackend,)
    filterset_class = DataSetFilter


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
        return get_allowed_objects_to_view_for_user(parent, self.request.user)


class MethodViewSet(viewsets.ModelViewSet):
    queryset = Method.objects.all()
    serializer_class = MethodSerializer

    filter_backends = (DjangoFilterBackend,)
    filterset_class = MethodFilter


# ===============================================================
# Parameter
# ===============================================================

class ParameterFilter(filters.FilterSet):
    project = filters.ModelChoiceFilter(queryset=Project.objects.all(), field_name="star__project", lookup_expr='exact')

    class Meta:
        model = Parameter
        fields = ['star', ]

    @property
    def qs(self):
        parent = super(ParameterFilter, self).qs

        parent = get_allowed_objects_to_view_for_user(parent, self.request.user)


class ParameterViewSet(viewsets.ModelViewSet):
    queryset = Parameter.objects.all()
    serializer_class = ParameterListSerializer

    filter_backends = (DjangoFilterBackend,)
    filterset_class = ParameterFilter


@api_view(['POST'])
def processDataSet(request, pk):
    success, message = process_datasets.process_analysis_file(pk)
    dataset = DataSet.objects.get(pk=pk)

    return Response(DataSetListSerializer(dataset).data)
