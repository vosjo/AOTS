from django.urls import include, re_path
from rest_framework import routers

from .plot_views import analysis_plots_api, parameter_plotter_api
from .views import (
    ParameterViewSet, AnalysisViewSet, processAnalysis, analysis_categories_api,
    upload_analyses_api,
)

app_name = 'analysis-api'

router = routers.DefaultRouter()
router.register(r'analyses', AnalysisViewSet)
router.register(r'parameters', ParameterViewSet)

urlpatterns = [
    re_path(
        r'^plotter/(?P<project_slug>[\w-]+)/$',
        parameter_plotter_api,
        name='parameter-plotter-api',
    ),
    re_path(
        r'^analyses/(?P<pk>[\w-]+)/plots/$',
        analysis_plots_api,
        name='analysis-plots-api',
    ),
    re_path(r'^categories/$', analysis_categories_api, name='analysis-categories-api'),
    re_path(r'^analyses/upload/$', upload_analyses_api, name='analysis-upload-api'),
    re_path(r'^', include(router.urls)),
    re_path(
        r'^analyses/(?P<pk>[\w-]+)/process/',
        processAnalysis,
        name='process_analysis',
    ),
]
