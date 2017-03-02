 
from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^stars/$', views.star_list, name='star_list'),
    url(r'^stars/(?P<star_id>[0-9]+)/$', views.star_detail, name='star_detail'),
    url(r'^stars/(?P<star_id>[0-9]+)/edit$', views.star_edit, name='star_edit'),
    url(r'^tags/$', views.tag_list, name='tag_list'),
]