from AOTS.custom_permissions import get_allowed_objects_to_view_for_user


class ProjectFilteredQuerysetMixin:
    """
    Restrict list querysets to projects the current user may view.
    """

    project_lookup = 'project'
    parameter_switch = False

    def get_queryset(self):
        qs = super().get_queryset()
        return get_allowed_objects_to_view_for_user(
            qs,
            self.request.user,
            parameter_switch=self.parameter_switch,
        )
