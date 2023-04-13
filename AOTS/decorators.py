# from django.contrib.auth.decorators import user_passes_test

from django.shortcuts import get_object_or_404

from stars.models import Project


def user_login_required_for_edit(function):
    '''
    Decorator for views that checks that the logged in user is a student,
    redirects to the log-in page if necessary.
    '''

    def wrap(request, *args, **kwargs):

        project = get_object_or_404(Project, slug=kwargs.get('project', None))

        if project in request.user.readonly_projects.objects.all():
            raise PermissionDenied

        elif project in request.user.readwriteown_projects.objects.all():
            if Star.objects.get(pk=kwargs['star_id']).history.earliest().history_user == request.user:
                return function(request, *args, **kwargs)
            else:
                raise PermissionDenied

        elif project in request.user.readwrite_projects.objects.all():
            return function(request, *args, **kwargs)

        else:
            raise PermissionDenied

    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap
