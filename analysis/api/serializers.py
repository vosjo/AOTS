from rest_framework.serializers import ModelSerializer, SerializerMethodField

from AOTS.page_urls import analysis_detail_url
from AOTS.serializer_mixins import ObjectPermissionFieldsMixin, ProjectFieldGuardMixin
from analysis.categories import category_color, category_label, category_derived_parameter_specs, has_category_derived_parameters
from analysis.models import Analysis, DerivedParameter, Parameter
from analysis.parameter_labels import parameter_label_with_unit, unit_display_name
from analysis.services.analysis_history import (
    added_by_display,
    earliest_iso,
    latest_iso,
    modified_by_username,
)
from analysis.services.parameter_consensus import consensus_queryset
from stars.api.serializers import SimpleStarSerializer


class AnalysisListSerializer(ObjectPermissionFieldsMixin, ProjectFieldGuardMixin, ModelSerializer):
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
            'can_edit',
            'can_delete',
        ]
        read_only_fields = ('pk', 'file_url', 'category_label', 'category_color', 'can_edit', 'can_delete')

    def get_added_on(self, obj):
        return earliest_iso(obj)

    def get_star(self, obj):
        if obj.star:
            return SimpleStarSerializer(obj.star).data
        return {}

    def get_category_label(self, obj):
        return category_label(obj.category)

    def get_category_color(self, obj):
        return category_color(obj.category)

    def get_href(self, obj):
        return analysis_detail_url(obj.project.slug, obj.pk)

    def get_file_url(self, obj):
        return obj.datafile.url


class AnalysisParameterSerializer(ModelSerializer):
    rvalue = SerializerMethodField()
    rerror = SerializerMethodField()
    display_label = SerializerMethodField()
    unit_display = SerializerMethodField()

    class Meta:
        model = Parameter
        fields = [
            'pk',
            'cname',
            'name',
            'component',
            'unit',
            'unit_display',
            'display_label',
            'value',
            'error',
            'rvalue',
            'rerror',
            'valid',
        ]
        read_only_fields = (
            'pk', 'cname', 'name', 'component', 'unit', 'unit_display',
            'display_label', 'value', 'error', 'rvalue', 'rerror',
        )

    def get_display_label(self, obj):
        return parameter_label_with_unit(obj.cname, obj.unit, from_cname=True)

    def get_unit_display(self, obj):
        return unit_display_name(obj.unit)

    def get_rvalue(self, obj):
        return obj.rvalue()

    def get_rerror(self, obj):
        return obj.rerror()


class AnalysisDetailSerializer(AnalysisListSerializer):
    reference_url = SerializerMethodField()
    parameters = SerializerMethodField()
    derived_parameters = SerializerMethodField()
    has_derived_definitions = SerializerMethodField()
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
            'derived_parameters',
            'has_derived_definitions',
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

    def get_derived_parameters(self, obj):
        if not obj.star_id or not has_category_derived_parameters(obj.category):
            return []
        specs = set(category_derived_parameter_specs(obj.category))
        derived = (
            consensus_queryset(star=obj.star)
            .filter(derivedparameter__isnull=False)
            .order_by('name', 'component')
        )
        return AnalysisParameterSerializer(
            [dpar for dpar in derived if (dpar.name, dpar.component) in specs],
            many=True,
        ).data

    def get_has_derived_definitions(self, obj):
        return has_category_derived_parameters(obj.category)

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

    def get_added_by(self, obj):
        return added_by_display(obj)

    def get_last_modified(self, obj):
        return latest_iso(obj)

    def get_modified_by(self, obj):
        return modified_by_username(obj)


class ParameterListSerializer(ModelSerializer):
    project = SerializerMethodField()
    parameter_source = SerializerMethodField()
    analysis = SerializerMethodField()

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
            'parameter_source',
            'analysis',
        ]
        read_only_fields = ('pk',)

    def get_project(self, obj):
        return obj.star.project.name

    def get_parameter_source(self, obj):
        if obj.parameter_source_id is None:
            return None
        return {'pk': obj.parameter_source_id, 'name': obj.parameter_source.name}

    def get_analysis(self, obj):
        if obj.analysis_id is None:
            return None
        return obj.analysis_id
