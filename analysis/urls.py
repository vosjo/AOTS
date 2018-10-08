 
from django.urls import path

from . import views

app_name = 'analysis'
urlpatterns = [
    path('datasets/', views.dataset_list, name='dataset_list'),
    path('datasets/<int:dataset_id>/', views.dataset_detail, name='dataset_detail'),
    path('methods', views.method_list, name='method_list'),
    path('plotter', views.parameter_plotter, name='parameter_plotter'),
]
