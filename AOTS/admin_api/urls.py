from django.urls import include, path
from rest_framework.routers import DefaultRouter

from AOTS.admin_api.views import (
    AdminGroupViewSet,
    AdminLogEntryViewSet,
    AdminProjectViewSet,
    AdminTokenViewSet,
    AdminUserViewSet,
    permissions_grouped,
    user_choices,
)

router = DefaultRouter()
router.register(r'users', AdminUserViewSet, basename='admin-user')
router.register(r'projects', AdminProjectViewSet, basename='admin-project')
router.register(r'groups', AdminGroupViewSet, basename='admin-group')
router.register(r'tokens', AdminTokenViewSet, basename='admin-token')
router.register(r'log-entries', AdminLogEntryViewSet, basename='admin-log-entry')

urlpatterns = [
    path('users/choices/', user_choices, name='admin-user-choices'),
    path('permissions/', permissions_grouped, name='admin-permissions'),
    path('', include(router.urls)),
]
