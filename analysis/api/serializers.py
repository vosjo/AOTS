from datetime import datetime

from astropy.time import Time
from django.urls import reverse
from rest_framework.serializers import ModelSerializer, SerializerMethodField

from analysis.models import Method, DataSet, Parameter
from stars.api.serializers import SimpleStarSerializer


class MethodSerializer(ModelSerializer):
    data_type_display = SerializerMethodField()

    class Meta:
        model = Method
        fields = [
            'pk',
            'name',
            'description',
            'slug',
            'color',
            'data_type',
            'data_type_display',
            'derived_parameters',
            'project'
        ]
        read_only_fields = ('pk',)

    def get_data_type_display(self, obj):
        return obj.get_data_type_display()


class DataSetListSerializer(ModelSerializer):
    star = SerializerMethodField()
    method = SerializerMethodField()
    href = SerializerMethodField()
    file_url = SerializerMethodField()
    added_on = SerializerMethodField()

    class Meta:
        model = DataSet
        fields = [
            'star',
            'pk',
            'name',
            'note',
            'method',
            'valid',
            'project',
            'href',
            'file_url',
            'datafile',
            'added_on',
        ]
        read_only_fields = ('pk', 'file_url',)
        datatables_always_serialize = ('pk', 'href', 'file_url')


    def get_added_on(self, obj):
        return Time(obj.history.earliest().history_date, precision=0).iso

    def get_star(self, obj):
        if obj.star:
            return SimpleStarSerializer(obj.star).data
        else:
            return {}

    def get_method(self, obj):
        if obj.method:
            return MethodSerializer(obj.method).data
        else:
            return {}

    def get_href(self, obj):
        return reverse(
            'analysis:dataset_detail',
            kwargs={'project': obj.project.slug, 'dataset_id': obj.pk},
        )

    def get_file_url(self, obj):
        return obj.datafile.url


class DatasetParameterSerializer(ModelSerializer):
    rvalue = SerializerMethodField()
    rerror = SerializerMethodField()

    class Meta:
        model = Parameter
        fields = [
            'pk',
            'cname',
            'name',
            'component',
            'unit',
            'value',
            'error',
            'rvalue',
            'rerror',
            'valid',
        ]
        read_only_fields = ('pk', 'cname', 'name', 'component', 'unit', 'value', 'error', 'rvalue', 'rerror')

    def get_rvalue(self, obj):
        return obj.rvalue()

    def get_rerror(self, obj):
        return obj.rerror()


class DataSetDetailSerializer(DataSetListSerializer):
    reference_url = SerializerMethodField()
    parameters = SerializerMethodField()
    related_datasets = SerializerMethodField()
    related_by_method = SerializerMethodField()
    added_by = SerializerMethodField()
    last_modified = SerializerMethodField()
    modified_by = SerializerMethodField()

    class Meta(DataSetListSerializer.Meta):
        fields = DataSetListSerializer.Meta.fields + [
            'reference',
            'reference_url',
            'parameters',
            'related_datasets',
            'related_by_method',
            'added_by',
            'last_modified',
            'modified_by',
        ]

    def get_reference_url(self, obj):
        return obj.get_reference_url()

    def get_parameters(self, obj):
        return DatasetParameterSerializer(obj.parameter_set.order(), many=True).data

    def get_related_datasets(self, obj):
        if not obj.star_id:
            return []
        related = DataSet.objects.filter(star_id=obj.star_id).select_related('method')
        return [
            {
                'pk': item.pk,
                'method_name': item.method.name if item.method else '',
                'is_current': item.pk == obj.pk,
            }
            for item in related
        ]

    def get_related_by_method(self, obj):
        if not obj.method_id:
            return []
        related = DataSet.objects.filter(method_id=obj.method_id).select_related('star')
        return [
            {
                'pk': item.pk,
                'star_name': item.star.name if item.star else '',
                'is_current': item.pk == obj.pk,
            }
            for item in related
        ]

    def _history_user_display(self, user):
        if user is None:
            return '—'
        full_name = f'{user.first_name} {user.last_name}'.strip()
        return full_name or user.username

    def get_added_by(self, obj):
        earliest = obj.history.earliest()
        return self._history_user_display(earliest.history_user)

    def get_last_modified(self, obj):
        return Time(obj.history.latest().history_date, precision=0).iso

    def get_modified_by(self, obj):
        latest = obj.history.latest()
        if latest.history_user is None:
            return '—'
        return latest.history_user.username


class ParameterListSerializer(ModelSerializer):
    project = SerializerMethodField()

    class Meta:
        model = Parameter
        fields = [
            'pk',
            'star',
            'name',
            'cname',
            'component',
            'value',
            'error',
            'unit',
            'valid',
            'project',
        ]
        read_only_fields = ('pk',)

    def get_project(self, obj):
        return obj.star.project.name

