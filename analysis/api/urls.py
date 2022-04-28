from django.urls import include, re_path
from rest_framework import routers

from .views import (
    ParameterViewSet, DatasetViewSet, MethodViewSet, processDataSet,
)

app_name = 'analysis-api'

router = routers.DefaultRouter()
router.register(r'methods', MethodViewSet)
router.register(r'datasets', DatasetViewSet)
router.register(r'parameters', ParameterViewSet)

urlpatterns = [
    ##url(r'^datasets$', DatasetListAPIView.as_view(), name='dataset_list'),
    re_path(r'^', include(router.urls)),
    re_path(r'^datasets/(?P<pk>[\w-]+)/process/',
            processDataSet,
            name='process_dataset',
            ),
]
