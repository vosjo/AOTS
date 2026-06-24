from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from AOTS.admin_api.permissions import IsSuperuser
from AOTS.pagination import AOTSPageNumberPagination
from AOTS.task_metadata import get_task_owner, list_task_ids
from AOTS.task_status import build_task_status_payload
from stars.models import Project

User = get_user_model()
ADMIN_PERMISSIONS = [IsAuthenticated, IsSuperuser]


def _enrich_tasks(tasks):
    user_ids = {t['user_id'] for t in tasks if t.get('user_id')}
    project_ids = {t['project_id'] for t in tasks if t.get('project_id')}

    users = {
        u.pk: u.username
        for u in User.objects.filter(pk__in=user_ids).only('pk', 'username')
    }
    projects = {
        p.pk: p.name
        for p in Project.objects.filter(pk__in=project_ids).only('pk', 'name')
    }

    for task in tasks:
        task['username'] = users.get(task.get('user_id'))
        task['project_name'] = projects.get(task.get('project_id'))


def _filter_tasks(request):
    search = request.query_params.get('search', '').strip().lower()
    active_only = request.query_params.get('active_only', '').lower() in ('1', 'true', 'yes')
    status_filter = request.query_params.get('status', '').strip().upper()

    tasks = []
    for task_id in list_task_ids():
        registration = get_task_owner(task_id)
        if registration is None:
            continue

        payload = build_task_status_payload(task_id, registration)
        if active_only and payload.get('ready'):
            continue
        if status_filter and payload.get('status') != status_filter:
            continue
        if search:
            haystack = ' '.join([
                task_id,
                registration.get('label') or '',
                registration.get('task_name') or '',
                payload.get('task_display') or '',
            ]).lower()
            if search not in haystack:
                continue
        tasks.append(payload)

    _enrich_tasks(tasks)
    return tasks


@api_view(['GET'])
@permission_classes(ADMIN_PERMISSIONS)
def admin_task_list(request):
    tasks = _filter_tasks(request)

    paginator = AOTSPageNumberPagination()
    page = paginator.paginate_queryset(tasks, request, view=None)
    if page is not None:
        return paginator.get_paginated_response(page)

    return Response({'count': len(tasks), 'results': tasks})


@api_view(['GET'])
@permission_classes(ADMIN_PERMISSIONS)
def admin_task_detail(request, task_id):
    registration = get_task_owner(task_id)
    payload = build_task_status_payload(task_id, registration)
    _enrich_tasks([payload])
    return Response(payload)
