from django.urls import path

from . import views

app_name = 'analysis'
urlpatterns = [
    path('analyses/', views.analysis_list, name='analysis_list'),
    path(
        'analyses/<int:analysis_id>/',
        views.analysis_detail,
        name='analysis_detail'
    ),
    path('methods', views.method_list, name='method_list'),
    path('plotter', views.parameter_plotter, name='parameter_plotter'),
]
