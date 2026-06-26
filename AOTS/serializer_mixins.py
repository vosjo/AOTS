"""Shared DRF serializer mixins for project-scoped models."""

from rest_framework import serializers


class ProjectCapabilityMixin(serializers.Serializer):
    """Per-user project capabilities for list/detail API responses."""

    can_add = serializers.SerializerMethodField()

    def get_can_add(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return request.user.can_add(obj)


class ObjectPermissionFieldsMixin(serializers.Serializer):
    """Per-object edit/delete flags for the authenticated user."""

    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()

    def get_can_edit(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return request.user.can_edit(obj)

    def get_can_delete(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return request.user.can_delete(obj)


class ProjectFieldGuardMixin:
    """
    Prevent moving existing rows to another project via the API and require
    can_add on the target project when project is supplied on create.
    """

    project_field_name = 'project'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance is not None and self.project_field_name in self.fields:
            self.fields[self.project_field_name].read_only = True

    def validate(self, attrs):
        attrs = super().validate(attrs)
        project_field = self.project_field_name
        if project_field not in attrs:
            return attrs

        new_project = attrs[project_field]
        if self.instance is not None:
            current_project_id = getattr(self.instance, f'{project_field}_id', None)
            if current_project_id is not None and new_project.pk != current_project_id:
                raise serializers.ValidationError({
                    project_field: 'Project cannot be changed after creation.',
                })
            return attrs

        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if user is None or not user.is_authenticated:
            raise serializers.ValidationError({
                project_field: 'Authentication required to assign a project.',
            })
        if not user.can_add(new_project):
            raise serializers.ValidationError({
                project_field: 'You do not have permission to add objects to this project.',
            })
        return attrs
