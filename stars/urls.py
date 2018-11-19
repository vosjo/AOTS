 
from django.urls import path

from . import views

app_name = 'systems'
urlpatterns = [
   path('stars/', views.star_list, name='star_list'),
   path('stars/<int:star_id>', views.star_detail, name='star_detail'),
   path('stars/<int:star_id>/edit', views.star_edit, name='star_edit'),
   path('tags/', views.tag_list, name='tag_list'),
]
