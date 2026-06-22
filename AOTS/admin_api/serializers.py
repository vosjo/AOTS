import json

from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from stars.models import Project

User = get_user_model()

ACTION_FLAG_LABELS = {
    ADDITION: 'Addition',
    CHANGE: 'Change',
    DELETION: 'Deletion',
}


class AdminUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'note',
            'is_active',
            'is_staff',
            'is_superuser',
            'is_student',
            'password',
        ]
        read_only_fields = ('id',)

    def validate(self, attrs):
        if self.instance is None and not attrs.get('password'):
            raise serializers.ValidationError({'password': 'This field is required.'})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        return User.objects.create_user(password=password, **validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class AdminUserChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username')


class AdminProjectSerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(required=False, allow_blank=True)
    readonly_users = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True,
        required=False,
    )
    readwriteown_users = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True,
        required=False,
    )
    readwrite_users = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True,
        required=False,
    )
    project_managers = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True,
        required=False,
    )

    class Meta:
        model = Project
        fields = [
            'pk',
            'name',
            'slug',
            'description',
            'is_public',
            'logo',
            'readonly_users',
            'readwriteown_users',
            'readwrite_users',
            'project_managers',
        ]
        read_only_fields = ('pk',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance is not None:
            self.fields['slug'].read_only = True

    def to_internal_value(self, data):
        mutable = data.copy() if hasattr(data, 'copy') else dict(data)
        for field in (
            'readonly_users',
            'readwriteown_users',
            'readwrite_users',
            'project_managers',
        ):
            if field in mutable and isinstance(mutable[field], str):
                try:
                    mutable[field] = json.loads(mutable[field])
                except json.JSONDecodeError:
                    pass
        return super().to_internal_value(mutable)

    def create(self, validated_data):
        m2m_data = self._pop_m2m(validated_data)
        if not validated_data.get('slug'):
            validated_data['slug'] = ''
        project = Project.objects.create(**validated_data)
        self._set_m2m(project, m2m_data)
        return project

    def update(self, instance, validated_data):
        m2m_data = self._pop_m2m(validated_data)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        self._set_m2m(instance, m2m_data)
        return instance

    @staticmethod
    def _pop_m2m(validated_data):
        return {
            'readonly_users': validated_data.pop('readonly_users', None),
            'readwriteown_users': validated_data.pop('readwriteown_users', None),
            'readwrite_users': validated_data.pop('readwrite_users', None),
            'project_managers': validated_data.pop('project_managers', None),
        }

    @staticmethod
    def _set_m2m(project, m2m_data):
        for field, value in m2m_data.items():
            if value is not None:
                getattr(project, field).set(value)


class AdminGroupSerializer(serializers.ModelSerializer):
    permission_count = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = ('id', 'name', 'permissions', 'permission_count')
        read_only_fields = ('id',)

    def get_permission_count(self, obj):
        return obj.permissions.count()


class AdminPermissionSerializer(serializers.ModelSerializer):
    app_label = serializers.CharField(source='content_type.app_label', read_only=True)
    model = serializers.CharField(source='content_type.model', read_only=True)

    class Meta:
        model = Permission
        fields = ('id', 'codename', 'name', 'app_label', 'model')


class AdminTokenSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Token
        fields = ('pk', 'key', 'user', 'username', 'created')
        read_only_fields = ('pk', 'key', 'created')

    def create(self, validated_data):
        user = validated_data['user']
        token, _created = Token.objects.get_or_create(user=user)
        return token


class AdminLogEntrySerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    app_label = serializers.CharField(source='content_type.app_label', read_only=True)
    model = serializers.CharField(source='content_type.model', read_only=True)
    action_flag_label = serializers.SerializerMethodField()
    change_message_display = serializers.SerializerMethodField()

    class Meta:
        model = LogEntry
        fields = (
            'id',
            'action_time',
            'user',
            'username',
            'content_type',
            'app_label',
            'model',
            'object_id',
            'object_repr',
            'action_flag',
            'action_flag_label',
            'change_message',
            'change_message_display',
        )
        read_only_fields = fields

    def get_username(self, obj):
        return obj.user.username if obj.user_id else None

    def get_action_flag_label(self, obj):
        return ACTION_FLAG_LABELS.get(obj.action_flag, str(obj.action_flag))

    def get_change_message_display(self, obj):
        return obj.get_change_message()
