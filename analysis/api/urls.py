from django.urls import include, re_path
from rest_framework import routers

from .plot_views import dataset_plots_api, parameter_plotter_api
from .views import (
    ParameterViewSet, DatasetViewSet, processDataSet, dataset_categories_api,
)

app_name = 'analysis-api'

router = routers.DefaultRouter()
router.register(r'datasets', DatasetViewSet)
router.register(r'parameters', ParameterViewSet)

urlpatterns = [
    re_path(
        r'^plotter/(?P<project_slug>[\w-]+)/$',
        parameter_plotter_api,
        name='parameter-plotter-api',
    ),
    re_path(
        r'^datasets/(?P<pk>[\w-]+)/plots/$',
        dataset_plots_api,
        name='dataset-plots-api',
    ),
    re_path(r'^categories/$', dataset_categories_api, name='dataset-categories-api'),
    re_path(r'^', include(router.urls)),
    re_path(
        r'^datasets/(?P<pk>[\w-]+)/process/',
        processDataSet,
        name='process_dataset',
    ),
]
