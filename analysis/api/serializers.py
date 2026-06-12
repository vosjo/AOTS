from astropy.time import Time
from django.urls import reverse
from rest_framework.serializers import ModelSerializer, SerializerMethodField

from analysis.categories import category_color, category_label
from analysis.models import Analysis, Parameter
from stars.api.serializers import SimpleStarSerializer


class AnalysisListSerializer(ModelSerializer):
    star = SerializerMethodField()
    category_label = SerializerMethodField()
    category_color = SerializerMethodField()
    href = SerializerMethodField()
    file_url = SerializerMethodField()
    added_on = SerializerMethodField()

    class Meta:
        model = Analysis
        fields = [
            'star',
            'pk',
            'name',
            'note',
            'category',
            'category_label',
            'category_color',
            'category_source',
            'file_type',
            'fit',
            'project',
            'href',
            'file_url',
            'datafile',
            'added_on',
        ]
        read_only_fields = ('pk', 'file_url', 'category_label', 'category_color')
        datatables_always_serialize = ('pk', 'href', 'file_url', 'category', 'category_label')

    def get_added_on(self, obj):
        return Time(obj.history.earliest().history_date, precision=0).iso

    def get_star(self, obj):
        if obj.star:
            return SimpleStarSerializer(obj.star).data
        return {}

    def get_category_label(self, obj):
        return category_label(obj.category)

    def get_category_color(self, obj):
        return category_color(obj.category)

    def get_href(self, obj):
        return reverse(
            'analysis:analysis_detail',
            kwargs={'project': obj.project.slug, 'analysis_id': obj.pk},
        )

    def get_file_url(self, obj):
        return obj.datafile.url


class AnalysisParameterSerializer(ModelSerializer):
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


class AnalysisDetailSerializer(AnalysisListSerializer):
    reference_url = SerializerMethodField()
    parameters = SerializerMethodField()
    related_analyses = SerializerMethodField()
    related_by_category = SerializerMethodField()
    added_by = SerializerMethodField()
    last_modified = SerializerMethodField()
    modified_by = SerializerMethodField()

    class Meta(AnalysisListSerializer.Meta):
        fields = AnalysisListSerializer.Meta.fields + [
            'reference',
            'reference_url',
            'parameters',
            'related_analyses',
            'related_by_category',
            'added_by',
            'last_modified',
            'modified_by',
        ]

    def get_reference_url(self, obj):
        return obj.get_reference_url()

    def get_parameters(self, obj):
        return AnalysisParameterSerializer(obj.parameter_set.order_by(), many=True).data

    def get_related_analyses(self, obj):
        if not obj.star_id:
            return []
        related = Analysis.objects.filter(star_id=obj.star_id).order_by('category', 'name')
        return [
            {
                'pk': item.pk,
                'name': item.name,
                'category': item.category,
                'category_label': category_label(item.category),
                'is_current': item.pk == obj.pk,
            }
            for item in related
        ]

    def get_related_by_category(self, obj):
        if not obj.category:
            return []
        related = Analysis.objects.filter(
            category=obj.category,
            project_id=obj.project_id,
        ).select_related('star').order_by('star__name', 'name')
        return [
            {
                'pk': item.pk,
                'star_name': item.star.name if item.star else '',
                'name': item.name,
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
