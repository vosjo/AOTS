from django.urls import path

from . import views

app_name = 'analysis'
urlpatterns = [
    ## Deprecated, will be removed in future ##
    path('datasets/', views.dataset_list, name='dataset_list'),
    path(
        'datasets/<int:dataset_id>/',
        views.dataset_detail,
        name='dataset_detail'
    ),
    path('methods', views.method_list, name='method_list'),
    ##

    path('rvcurves/', views.rvcurve_list, name='rvcurve_list'),
    path(
        'rvcurves/<int:rvcurve_id>/',
        views.rvcurve_detail,
        name='rvcurve_detail'
    ),

    path('seds/', views.SED_list, name='SED_list'),
    path(
        'seds/<int:sed_id>/',
        views.SED_detail,
        name='SED_detail'
    ),

    path('plotter', views.parameter_plotter, name='parameter_plotter'),

]
