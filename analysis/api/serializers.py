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

    class Meta:
        model = DataSet
        fields = [
            'star',
            'pk',
            'name',
            'note',
            'method',
            'valid',
            'added_on',
            'project',
            'href',
            'modified_by',
            'file_url',
            'datafile',
        ]
        read_only_fields = ('pk', 'file_url',)

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


class ParameterListSerializer(ModelSerializer):
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
        ]
        read_only_fields = ('pk',)
