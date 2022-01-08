from django.urls import include, path

from rest_framework import routers

from .views import (
   ProjectViewSet,
   StarViewSet, #star_remove_tag, star_add_tag,
   TagViewSet,
   IdentifierViewSet,
   getStarSpecfiles,
   )

app_name = 'stars-api'

router = routers.DefaultRouter()
router.register(r'stars', StarViewSet)
router.register(r'tags', TagViewSet)
router.register(r'identifiers', IdentifierViewSet, basename='identifier')

urlpatterns = [
   #url(r'^stars', StarListAPIView.as_view(), name='star_list'),

   #url(r'^', include(router.urls)),

   #url(r'^stars/(?P<star_pk>[\w-]+)/remove_tag/(?P<tag_pk>[\w-]+)/$', star_remove_tag,
       #name='star_remove_tag'),
   #url(r'^stars/(?P<star_pk>[\w-]+)/add_tag/(?P<tag_pk>[\w-]+)/$', star_add_tag,
       #name='star_add_tag'),

   #url(r'^tags$', TagListAPIView.as_view(), name='tag_list'),
   #url(r'^tags/create/$', TagCreateAPIView.as_view(), name='tag_create'),
   ##url(r'^tags/(?P<pk>[\w-]+)/$', TagDetailAPIView.as_view(), name='tag_detail'),
   #url(r'^tags/(?P<pk>[\w-]+)/delete/$', TagDeleteAPIView.as_view(), name='tag_delete'),

   #url(r'^identifiers$', IdentifierListAPIView.as_view(), name='identifier_list'),

   path('', include(router.urls) ),
   path(
       'stars/<int:star_pk>/specfiles/',
       getStarSpecfiles,
       name='stars_specfiles',
       ),
]
