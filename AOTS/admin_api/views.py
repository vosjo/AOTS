from django.contrib.admin.models import LogEntry
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django_filters import rest_framework as filters
from rest_framework import mixins, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from AOTS.admin_api.permissions import IsSuperuser
from AOTS.admin_api.serializers import (
    AdminGroupSerializer,
    AdminLogEntrySerializer,
    AdminPermissionSerializer,
    AdminProjectSerializer,
    AdminTokenSerializer,
    AdminUserChoiceSerializer,
    AdminUserSerializer,
)
from AOTS.pagination import AOTSPageNumberPagination
from stars.models import Project

User = get_user_model()

ADMIN_PERMISSIONS = [IsAuthenticated, IsSuperuser]


class AdminUserFilter(filters.FilterSet):
    class Meta:
        model = User
        fields = ['is_staff', 'is_superuser', 'is_active', 'is_student']


class AdminUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.order_by('username')
    serializer_class = AdminUserSerializer
    permission_classes = ADMIN_PERMISSIONS
    pagination_class = AOTSPageNumberPagination
    filter_backends = (filters.DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_class = AdminUserFilter
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)

    def perform_destroy(self, instance):
        if instance.pk == self.request.user.pk:
            raise ValidationError('Cannot delete your own account.')
        instance.delete()


class AdminProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.order_by('name')
    serializer_class = AdminProjectSerializer
    permission_classes = ADMIN_PERMISSIONS
    pagination_class = AOTSPageNumberPagination
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    filter_backends = (SearchFilter, OrderingFilter)
    search_fields = ('name', 'slug', 'description')
    ordering_fields = ('name', 'slug')
    ordering = ('name',)

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError as exc:
            raise ValidationError(
                'Cannot delete this project because related observation data is still in use.',
            ) from exc


class AdminGroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.prefetch_related('permissions').order_by('name')
    serializer_class = AdminGroupSerializer
    permission_classes = ADMIN_PERMISSIONS
    pagination_class = AOTSPageNumberPagination
    filter_backends = (SearchFilter, OrderingFilter)
    search_fields = ('name',)
    ordering = ('name',)


class AdminTokenViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Token.objects.select_related('user').order_by('-created')
    serializer_class = AdminTokenSerializer
    permission_classes = ADMIN_PERMISSIONS
    pagination_class = AOTSPageNumberPagination
    filter_backends = (SearchFilter, OrderingFilter)
    search_fields = ('key', 'user__username')
    ordering_fields = ('created', 'key')
    ordering = ('-created',)


class AdminLogEntryViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = LogEntry.objects.select_related('user', 'content_type').order_by('-action_time')
    serializer_class = AdminLogEntrySerializer
    permission_classes = ADMIN_PERMISSIONS
    pagination_class = AOTSPageNumberPagination
    filter_backends = (SearchFilter, OrderingFilter)
    search_fields = ('object_repr', 'change_message', 'user__username')
    ordering_fields = ('action_time',)
    ordering = ('-action_time',)


@api_view(['GET'])
@permission_classes(ADMIN_PERMISSIONS)
def user_choices(request):
    qs = User.objects.order_by('username')
    search = request.query_params.get('search', '').strip()
    if search:
        qs = qs.filter(
            Q(username__icontains=search)
            | Q(email__icontains=search)
            | Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
        )
    paginator = AOTSPageNumberPagination()
    page = paginator.paginate_queryset(qs, request)
    serializer = AdminUserChoiceSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes(ADMIN_PERMISSIONS)
def permissions_grouped(request):
    perms = Permission.objects.select_related('content_type').order_by(
        'content_type__app_label',
        'content_type__model',
        'codename',
    )
    grouped = {}
    for perm in perms:
        key = f'{perm.content_type.app_label}.{perm.content_type.model}'
        if key not in grouped:
            grouped[key] = {
                'app_label': perm.content_type.app_label,
                'model': perm.content_type.model,
                'permissions': [],
            }
        grouped[key]['permissions'].append(AdminPermissionSerializer(perm).data)
    return Response(list(grouped.values()))
