from datetime import datetime

from astropy.time import Time
from django.urls import reverse
from rest_framework.serializers import ModelSerializer, SerializerMethodField

from analysis.models import Method, DataSet, Parameter
from analysis.models.SEDs import SED
from analysis.models.rvcurves import RVcurve
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


class SEDSerializer(ModelSerializer):
    star = SerializerMethodField()
    href = SerializerMethodField()

    class Meta:
        model = SED
        fields = [
            'pk',
            'star',
            'project',
            'teff',
            'teff_lerr',
            'teff_uerr',
            'logg',
            'logg_lerr',
            'logg_uerr',
            'metallicity',
            'metallicity_lerr',
            'metallicity_uerr',
            'color_excess',
            'color_excess_lerr',
            'color_excess_uerr',
            'logtheta',
            'logtheta_lerr',
            'logtheta_uerr',
            # 'sedfile',
            'note',
            'href',
        ]
        read_only_fields = ('pk',)

    def get_href(self, obj):
        return reverse('analysis:SED_detail', kwargs={'project': obj.project.slug, 'sed_id': obj.pk})

    def get_star(self, obj):
        if obj.star:
            return SimpleStarSerializer(obj.star).data
        else:
            return {}


class RVcurveSerializer(ModelSerializer):
    star = SerializerMethodField()
    # rvcurvefile = SerializerMethodField()
    href = SerializerMethodField()

    class Meta:
        model = RVcurve
        fields = [
            'pk',
            'star',
            'project',
            'time_spanned',
            'N_samples',
            'average_rv',
            'average_rv_err',
            'delta_rv',
            'delta_rv_err',
            'half_amplitude',
            'solved',
            'logp',
            # 'rvcurvefile',
            'note',
            'href',
        ]
        read_only_fields = ('pk',)

    def get_href(self, obj):
        return reverse('analysis:rvcurve_detail', kwargs={'project': obj.project.slug, 'rvcurve_id': obj.pk})

    def get_star(self, obj):
        if obj.star:
            return SimpleStarSerializer(obj.star).data
        else:
            return {}
