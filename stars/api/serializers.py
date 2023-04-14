import numpy as np
from django.urls import reverse
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


class TagListSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = [
            'star',
            'name',
            'description',
            'color',
            'pk',
        ]
        read_only_fields = ('pk',)


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

class StarListSerializer(ModelSerializer):
    tags = SerializerMethodField()
    datasets = SerializerMethodField()
    vmag = SerializerMethodField()
    href = SerializerMethodField()
    nphot = SerializerMethodField()
    nspec = SerializerMethodField()
    nlc = SerializerMethodField()
    classification_type_display = SerializerMethodField()
    observing_status_display = SerializerMethodField()
    tag_ids = PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        read_only=False,
        source='tags',
    )

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
            'datasets',
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

    def get_datasets(self, obj):
        try:
            datasets = obj.dataset_set.all()
            return [{'name': d.name, 'color': d.method.color,
                     'href': reverse('analysis:dataset_detail', kwargs={'project': d.project.slug, 'dataset_id': d.pk})}
                    for d in datasets]
        except Exception as e:
            print(e)
            return []

    def get_vmag(self, obj):
        mag = obj.photometry_set.filter(band__icontains='GAIA2.G')
        return 0 if len(mag) == 0 else np.round(mag[0].measurement, 2)

    def get_href(self, obj):
        return reverse('systems:star_detail', kwargs={'project': obj.project.slug, 'star_id': obj.pk})

    def get_nphot(self, obj):
        return len(obj.photometry_set.all())

    def get_nspec(self, obj):
        return len(obj.spectrum_set.all())

    def get_nlc(self, obj):
        return len(obj.lightcurve_set.all())

    def get_classification_type_display(self, obj):
        return obj.get_classification_type_display()

    def get_observing_status_display(self, obj):
        return obj.get_observing_status_display()


class StarSerializer(ModelSerializer):
    tags = SerializerMethodField()
    tag_ids = PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        read_only=False,
        source='tags',
    )
    vmag = SerializerMethodField()
    href = SerializerMethodField()
    classification_type_display = SerializerMethodField()
    observing_status_display = SerializerMethodField()

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
