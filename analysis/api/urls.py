from django.urls import include, re_path
from rest_framework import routers

from .plot_views import analysis_plots_api, parameter_plotter_api
from .consensus_views import (
    consensus_policies_list_create,
    consensus_policies_meta,
    consensus_policy_detail,
)
from .views import (
    ParameterViewSet, AnalysisViewSet, analysis_categories_api,
    upload_analyses_api, derive_analysis_parameters_api,
)

app_name = 'analysis-api'

router = routers.DefaultRouter()
router.register(r'analyses', AnalysisViewSet)
router.register(r'parameters', ParameterViewSet)

urlpatterns = [
    re_path(
        r'^consensus-policies/(?P<project_slug>[\w-]+)/meta/$',
        consensus_policies_meta,
        name='consensus-policies-meta',
    ),
    re_path(
        r'^consensus-policies/(?P<project_slug>[\w-]+)/(?P<pk>\d+)/$',
        consensus_policy_detail,
        name='consensus-policy-detail',
    ),
    re_path(
        r'^consensus-policies/(?P<project_slug>[\w-]+)/$',
        consensus_policies_list_create,
        name='consensus-policies',
    ),
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
    re_path(
        r'^analyses/(?P<pk>[\w-]+)/derive-parameters/$',
        derive_analysis_parameters_api,
        name='analysis-derive-parameters-api',
    ),
    re_path(r'^', include(router.urls)),
]
