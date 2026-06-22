import numpy as np
from django.urls import reverse
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer, SerializerMethodField, PrimaryKeyRelatedField

from stars.models import Project, Star, Tag, Identifier


# ===============================================================
# PROJECTS
# ===============================================================

class ProjectListSerializer(ModelSerializer):
    class Meta:
        model = Project
        fields = [
            'name',
            'description',
            'slug',
            'pk',
            'is_public',
            'logo',
        ]
        read_only_fields = ('pk',)


class ProjectSerializer(ModelSerializer):
    class Meta:
        model = Project
        fields = [
            'name',
            'description',
            'slug',
            'logo',
            'pk',
        ]
        read_only_fields = ('pk',)


# ===============================================================
# TAGS
# ===============================================================


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = [
            'name',
            'project',
            'description',
            'color',
            'pk',
        ]
        read_only_fields = ('pk',)


class SimpleTagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = [
            'name',
            'color',
            'description',
        ]


# ===============================================================
# STARS
# ===============================================================

def _tag_queryset_for_serializer(serializer):
    project = None
    instance = getattr(serializer, 'instance', None)
    if isinstance(instance, Star):
        project = instance.project
    elif isinstance(instance, list) and instance:
        stars = [item for item in instance if isinstance(item, Star)]
        if stars:
            project_ids = {star.project_id for star in stars}
            if len(project_ids) == 1:
                project = stars[0].project
    if project is None:
        initial = getattr(serializer, 'initial_data', None) or {}
        project_pk = initial.get('project') if isinstance(initial, dict) else None
        if project_pk is not None:
            try:
                project = Project.objects.get(pk=int(project_pk))
            except (Project.DoesNotExist, TypeError, ValueError):
                project = None
    if project is None:
        return Tag.objects.none()
    return Tag.objects.filter(project=project)


def _scope_star_tag_ids_queryset(serializer):
    if 'tag_ids' not in serializer.fields:
        return
    queryset = _tag_queryset_for_serializer(serializer)
    field = serializer.fields['tag_ids']
    if isinstance(field, serializers.ManyRelatedField):
        field.child_relation.queryset = queryset
    else:
        field.queryset = queryset


class StarListSerializer(ModelSerializer):
    tags = SerializerMethodField()
    analyses = SerializerMethodField()
    vmag = SerializerMethodField()
    href = SerializerMethodField()
    nphot = SerializerMethodField()
    nspec = SerializerMethodField()
    nlc = SerializerMethodField()
    classification_type_display = SerializerMethodField()
    observing_status_display = SerializerMethodField()
    tag_ids = PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.none(),
        read_only=False,
        source='tags',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _scope_star_tag_ids_queryset(self)

    class Meta:
        model = Star
        fields = [
            'pk',
            'name',
            'project',
            'ra',
            'dec',
            'ra_hms',
            'dec_dms',
            'classification',
            'classification_type',
            'classification_type_display',
            'observing_status',
            'observing_status_display',
            'note',
            'tags',
            'analyses',
            'tag_ids',
            'vmag',
            'nphot',
            'nspec',
            'nlc',
            'href',
        ]
        read_only_fields = ('pk',)

        datatables_always_serialize = ('href', 'pk')

    def get_tags(self, obj):
        tags = TagSerializer(obj.tags, many=True).data
        return tags

    def get_analyses(self, obj):
        from analysis.categories import category_color, category_label

        try:
            analyses = obj.analysis_set.all()
            return [
                {
                    'name': f"{category_label(d.category)}: {d.name}" if d.name else category_label(d.category),
                    'color': category_color(d.category),
                    'href': reverse(
                        'analysis:analysis_detail',
                        kwargs={'project': d.project.slug, 'analysis_id': d.pk},
                    ),
                }
                for d in analyses
            ]
        except Exception as e:
            print(e)
            return []

    def get_vmag(self, obj):
        mag = obj.photometry_set.filter(band__icontains='GAIA2.G')
        return 0 if len(mag) == 0 else np.round(mag[0].measurement, 2)

    def get_href(self, obj):
        return reverse('systems:star_detail', kwargs={'project': obj.project.slug, 'star_id': obj.pk})

    def get_nphot(self, obj):
        if hasattr(obj, 'nphot_count'):
            return obj.nphot_count
        return obj.photometry_set.count()

    def get_nspec(self, obj):
        if hasattr(obj, 'nspec_count'):
            return obj.nspec_count
        return obj.spectrum_set.count()

    def get_nlc(self, obj):
        if hasattr(obj, 'nlc_count'):
            return obj.nlc_count
        return obj.lightcurve_set.count()

    def get_classification_type_display(self, obj):
        return obj.get_classification_type_display()

    def get_observing_status_display(self, obj):
        return obj.get_observing_status_display()

    def validate(self, attrs):
        attrs = super().validate(attrs)
        project = attrs.get('project') or (self.instance.project if self.instance else None)
        tags = attrs.get('tags')
        if project is not None and tags is not None:
            invalid = [tag.pk for tag in tags if tag.project_id != project.pk]
            if invalid:
                raise serializers.ValidationError({
                    'tag_ids': 'Tags must belong to the same project as the star.',
                })
        return attrs


class StarSerializer(ModelSerializer):
    tags = SerializerMethodField()
    tag_ids = PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.none(),
        read_only=False,
        source='tags',
    )
    vmag = SerializerMethodField()
    href = SerializerMethodField()
    classification_type_display = SerializerMethodField()
    observing_status_display = SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _scope_star_tag_ids_queryset(self)

    class Meta:
        model = Star
        fields = [
            'pk',
            'name',
            'project',
            'ra',
            'dec',
            'ra_hms',
            'dec_dms',
            'classification',
            'classification_type',
            'classification_type_display',
            'observing_status',
            'observing_status_display',
            'note',
            'tags',
            'tag_ids',
            'vmag',
            'href',
        ]
        read_only_fields = ('pk', 'tags', 'vmag',
                            'classification_type_display', 'observing_status_display')

    def get_tags(self, obj):
        # this has to be used instead of a through field, as otherwise
        # PUT or PATCH requests fail!
        tags = TagSerializer(obj.tags, many=True).data
        return tags

    def get_vmag(self, obj):
        mag = obj.photometry_set.filter(band__icontains='JOHNSON.V')
        return 0 if len(mag) == 0 else np.round(mag[0].measurement, 2)

    def get_href(self, obj):
        return reverse('systems:star_detail', kwargs={'project': obj.project.slug, 'star_id': obj.pk})

    def get_classification_type_display(self, obj):
        return obj.get_classification_type_display()

    def get_observing_status_display(self, obj):
        return obj.get_observing_status_display()

    def validate(self, attrs):
        attrs = super().validate(attrs)
        project = attrs.get('project') or (self.instance.project if self.instance else None)
        tags = attrs.get('tags')
        if project is not None and tags is not None:
            invalid = [tag.pk for tag in tags if tag.project_id != project.pk]
            if invalid:
                raise serializers.ValidationError({
                    'tag_ids': 'Tags must belong to the same project as the star.',
                })
        return attrs


class SimpleStarSerializer(ModelSerializer):
    """
    Basic serializer only returning the most basic information available for the Star object.
    """

    href = SerializerMethodField()

    class Meta:
        model = Star
        fields = [
            'pk',
            'name',
            'project',
            'ra',
            'dec',
            'href',
        ]
        read_only_fields = ('pk',)

    def get_href(self, obj):
        return reverse('systems:star_detail', kwargs={'project': obj.project.slug, 'star_id': obj.pk})


# ===============================================================
# IDENTIFIERS
# ===============================================================

class IdentifierListSerializer(ModelSerializer):
    class Meta:
        model = Identifier
        fields = [
            'pk',
            'star',
            'project',
            'name',
            'href',
        ]
        read_only_fields = ('pk', 'project')
