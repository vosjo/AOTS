
from django.urls import path
from django.views.generic.base import RedirectView
from django.contrib.staticfiles.storage import staticfiles_storage

from . import views

app_name = 'systems'
urlpatterns = [
    path('stars/', views.star_list, name='star_list'),
    path('stars/<int:star_id>', views.star_detail, name='star_detail'),
    path('stars/<int:star_id>/edit', views.star_edit, name='star_edit'),
    path('tags/', views.tag_list, name='tag_list'),
    path(
        "favicon.ico",
        RedirectView.as_view(url=staticfiles_storage.url("favicon.ico")),
    ),
]
