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


class DatatablesOrderingMixin:
    """
    Apply DataTables column ordering from query parameters.
    """

    default_ordering = ('pk',)

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        return self.apply_datatables_ordering(queryset)

    def apply_datatables_ordering(self, queryset):
        getter = self.request.query_params.get
        order_column = getter('order[0][column]')
        if order_column is None:
            return queryset.order_by(*self.default_ordering)

        order_name = getter('columns[%s][data]' % order_column)
        if getter('order[0][dir]') == 'desc':
            order_name = '-' + order_name

        allowed = getattr(self, 'allowed_order_fields', None)
        if allowed is not None:
            field_name = order_name.lstrip('-')
            if field_name not in allowed:
                return queryset.order_by(*self.default_ordering)

        return queryset.order_by(order_name)
