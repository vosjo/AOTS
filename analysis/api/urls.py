from django.urls import include, re_path
from rest_framework import routers

from .consensus_views import (
    consensus_policies_list_create,
    consensus_policies_meta,
    consensus_policy_detail,
)
from .fit_views import (
    analysis_best_fit_api,
    analysis_fit_detail_api,
    analysis_fit_parameters_api,
    analysis_fits_api,
    contribute_lc_fit_api,
    contribute_spectral_fit_api,
    contribute_star_fit_api,
)
from .plot_views import analysis_plots_api, parameter_plotter_api
from .views import (
    AnalysisViewSet,
    ParameterViewSet,
    analysis_categories_api,
    analysis_redirect_api,
    derive_analysis_parameters_api,
    upload_analyses_api,
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
    re_path(
        r'^analyses/(?P<pk>[\w-]+)/redirect/$',
        analysis_redirect_api,
        name='analysis-redirect-api',
    ),
    re_path(r'^analyses/upload/$', upload_analyses_api, name='analysis-upload-api'),
    re_path(
        r'^analyses/(?P<pk>[\w-]+)/derive-parameters/$',
        derive_analysis_parameters_api,
        name='analysis-derive-parameters-api',
    ),
    re_path(
        r'^analyses/(?P<pk>[\w-]+)/fits/$',
        analysis_fits_api,
        name='analysis-fits-api',
    ),
    re_path(
        r'^analyses/(?P<pk>[\w-]+)/fits/(?P<fit_id>[^/]+)/$',
        analysis_fit_detail_api,
        name='analysis-fit-detail-api',
    ),
    re_path(
        r'^analyses/(?P<pk>[\w-]+)/best-fit/$',
        analysis_best_fit_api,
        name='analysis-best-fit-api',
    ),
    re_path(
        r'^analyses/(?P<pk>[\w-]+)/fit-parameters/$',
        analysis_fit_parameters_api,
        name='analysis-fit-parameters-api',
    ),
    re_path(
        r'^contribute/spectral/(?P<spectrum_pk>[\w-]+)/$',
        contribute_spectral_fit_api,
        name='contribute-spectral-fit-api',
    ),
    re_path(
        r'^contribute/lightcurve/(?P<lightcurve_pk>[\w-]+)/$',
        contribute_lc_fit_api,
        name='contribute-lc-fit-api',
    ),
    re_path(
        r'^contribute/star/(?P<star_pk>[\w-]+)/$',
        contribute_star_fit_api,
        name='contribute-star-fit-api',
    ),
    re_path(r'^categories/$', analysis_categories_api, name='analysis-categories-api'),
    re_path(r'^', include(router.urls)),
]
