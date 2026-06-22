"""
Shared helpers for synchronous/async entity processing API views.
"""

from rest_framework.response import Response
from rest_framework import status

from AOTS.task_helpers import run_task


def run_process_view(request, obj, task, serializer_class, async_kwarg='async'):
    """
    Run a processing task sync or async; return DRF Response.
    """
    async_requested = request.query_params.get(async_kwarg) == '1'
    task_kwargs = {}
    if request.user.is_authenticated:
        task_kwargs['history_user_id'] = request.user.pk
    _, task_id = run_task(
        task,
        obj.pk,
        async_requested=async_requested,
        owner_user_id=request.user.pk if request.user.is_authenticated else None,
        **task_kwargs,
    )
    if task_id:
        return Response(
            {'status': 'pending', 'task_id': task_id},
            status=status.HTTP_202_ACCEPTED,
        )
    obj.refresh_from_db()
    return Response(serializer_class(obj).data)
