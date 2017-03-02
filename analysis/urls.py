 
from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^datasets/$', views.dataset_list, name='dataset_list'),
    url(r'^datasets/(?P<dataset_id>[0-9]+)/$', views.dataset_detail, name='dataset_detail'),
    url(r'^methods', views.method_list, name='method_list'),
    url(r'^plotter', views.parameter_plotter, name='parameter_plotter'),
]