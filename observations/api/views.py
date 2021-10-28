
#from rest_framework.generics import (
   #CreateAPIView,
   #DestroyAPIView,
   #ListAPIView,
   #UpdateAPIView,
   #RetrieveAPIView,
   #RetrieveUpdateAPIView
#)

from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import api_view

from .serializers import SpectrumSerializer, SpectrumListSerializer, SpecFileSerializer,LightCurveSerializer, ObservatorySerializer

from observations.models import Spectrum, SpecFile, LightCurve, Observatory

from observations.auxil import read_spectrum, read_lightcurve

from AOTS.custom_permissions import get_allowed_objects_to_view_for_user, check_user_can_view_project

# ===============================================================
# Spectrum
# ===============================================================

class SpectrumFilter(filters.FilterSet):

   target = filters.CharFilter(field_name="target", method="star_name_icontains", lookup_expr='icontains')

   hjd_min = filters.NumberFilter(field_name="hjd", lookup_expr='gte')
   hjd_max = filters.NumberFilter(field_name="hjd", lookup_expr='lte')

   exptime_min = filters.NumberFilter(field_name="exptime", lookup_expr='gte')
   exptime_max = filters.NumberFilter(field_name="exptime", lookup_expr='lte')

   instrument = filters.CharFilter(field_name="instrument", lookup_expr='icontains')

   telescope = filters.CharFilter(field_name="telescope", lookup_expr='icontains')

   fluxcal = filters.BooleanFilter(field_name='fluxcal')

   def star_name_icontains(self, queryset, name, value):
      return queryset.filter(star__name__icontains=value)

   class Meta:
      model = Spectrum
      fields = ['project',]

   @property
   def qs(self):
      parent = super(SpectrumFilter, self).qs

      parent = get_allowed_objects_to_view_for_user(parent, self.request.user)

      # get the column order from the GET dictionary
      getter = self.request.query_params.get
      if not getter('order[0][column]') is None:
         order_column = int(getter('order[0][column]'))
         order_name = getter('columns[%i][data]' % order_column)
         if getter('order[0][dir]') == 'desc': order_name = '-'+order_name

         return parent.order_by(order_name)
      else:
         return parent


class SpectrumViewSet(viewsets.ModelViewSet):
   queryset = Spectrum.objects.all()
   serializer_class = SpectrumSerializer

   filter_backends = (DjangoFilterBackend,)
   filterset_class = SpectrumFilter


@api_view(['POST'])
def processSpectrum(request, spectrum_pk):
   success, message = read_spectrum.derive_spectrum_info(spectrum_pk)
   spectrum = Spectrum.objects.get(pk=spectrum_pk)

   return Response(SpectrumSerializer(spectrum).data)


@check_user_can_view_project
def spectrum_plot(request, spectrum_id, project=None,  **kwargs):
    '''
    View to plot only the spectrum to allow asynchronous loading
    '''

    #   Load project and spectrum
    project = get_object_or_404(Project, slug=project)
    spectrum = get_object_or_404(Spectrum, pk=spectrum_id)

    #   Check if spectrum should be rebinned
    #   -> those larger than 1 Mb get rebinned
    total_size = sum([s.specfile.size for s in spectrum.specfile_set.all()])
    if total_size > 500000:
        rebin = 10
        #request.GET._mutable = True
        #request.GET['rebin'] = 10
    else:
        rebin = 1

    #   Specify normalisation
    normalize = True

    #   Check if user specified binning factor and normalization
    if request.method == 'GET':
        rebin     = int(request.GET.get('rebin', rebin))
        normalize = bool(int(request.GET.get('normalize', normalize)))

    #   Make plots
    #vis  = plot_visibility(spectrum)
    spec = plot_spectrum(spectrum_id, rebin=rebin, normalize=normalize)

    #   Create HTML content
    #script, div = components({'spec':spec, 'visibility':vis}, CDN)
    script, div = components({'spec':spec}, CDN)

    #   Make dict with the content
    context = {
        #'project': project,
        #'spectrum': spectrum,
        'figures': div,
        'script': script,
    }

    return render_to_response('spectrum_plot.html', context)


# ===============================================================
# SpecFile
# ===============================================================

class SpecFileFilter(filters.FilterSet):

   target = filters.CharFilter(field_name="target", method="star_name_icontains", lookup_expr='icontains')

   hjd_min = filters.NumberFilter(field_name="hjd", lookup_expr='gte')
   hjd_max = filters.NumberFilter(field_name="hjd", lookup_expr='lte')

   instrument = filters.CharFilter(field_name="instrument", lookup_expr='icontains')

   #processed = filters.BooleanFilter(field_name="Processed", method="is_processed")

   def star_name_icontains(self, queryset, name, value):
      return queryset.filter(spectrum__star__name__icontains=value)

   #def is_processed(self, queryset, name, value):
      #return False

   class Meta:
      model = SpecFile
      fields = ['project',]

   @property
   def qs(self):
      parent = super(SpecFileFilter, self).qs

      parent = get_allowed_objects_to_view_for_user(parent, self.request.user)

      # get the column order from the GET dictionary
      getter = self.request.query_params.get
      if not getter('order[0][column]') is None:
         order_column = int(getter('order[0][column]'))
         order_name = getter('columns[%i][data]' % order_column)
         if getter('order[0][dir]') == 'desc': order_name = '-'+order_name

         return parent.order_by(order_name)
      else:
         return parent

class SpecFileViewSet(viewsets.ModelViewSet):
   queryset = SpecFile.objects.all()
   serializer_class = SpecFileSerializer

   filter_backends = (DjangoFilterBackend,)
   filterset_class = SpecFileFilter



@api_view(['POST'])
def processSpecfile(request, specfile_pk):
   success, message = read_spectrum.process_specfile(specfile_pk)
   specfile = SpecFile.objects.get(pk=specfile_pk)

   return Response(SpecFileSerializer(specfile).data)

@api_view(['GET'])
def getSpecfileHeader(request, specfile_pk):
   specfile = SpecFile.objects.get(pk=specfile_pk)
   header = specfile.get_header()

   return Response(header)


# ===============================================================
# LightCurve
# ===============================================================

class LightCurveFilter(filters.FilterSet):

   target = filters.CharFilter(field_name="target", method="star_name_icontains", lookup_expr='icontains')

   hjd_min = filters.NumberFilter(field_name="hjd", lookup_expr='gte')
   hjd_max = filters.NumberFilter(field_name="hjd", lookup_expr='lte')

   instrument = filters.CharFilter(field_name="instrument", lookup_expr='icontains')

   def star_name_icontains(self, queryset, name, value):
      return queryset.filter(spectrum__star__name__icontains=value)

   class Meta:
      model = LightCurve
      fields = ['project',]

   @property
   def qs(self):
      parent = super(LightCurveFilter, self).qs

      parent = get_allowed_objects_to_view_for_user(parent, self.request.user)

      # get the column order from the GET dictionary
      getter = self.request.query_params.get
      if not getter('order[0][column]') is None:
         order_column = int(getter('order[0][column]'))
         order_name = getter('columns[%i][data]' % order_column)
         if getter('order[0][dir]') == 'desc': order_name = '-'+order_name

         return parent.order_by(order_name)
      else:
         return parent

class LightCurveViewSet(viewsets.ModelViewSet):
   queryset = LightCurve.objects.all()
   serializer_class = LightCurveSerializer

   filter_backends = (DjangoFilterBackend,)
   filterset_class = LightCurveFilter


@api_view(['POST'])
def processLightCurve(request, lightcurve_pk):
   success, message = read_lightcurve.process_lightcurve(lightcurve_pk)
   lightcurve = LightCurve.objects.get(pk=lightcurve_pk)

   return Response(LightCurveSerializer(lightcurve).data)


@api_view(['GET'])
def getLightCurveHeader(request, lightcurve_pk):
   lightcurve = LightCurve.objects.get(pk=lightcurve_pk)
   header = lightcurve.get_header()

   return Response(header)

# ===============================================================
# Observatory
# ===============================================================

class ObservatoryFilter(filters.FilterSet):

   name = filters.CharFilter(field_name="name", lookup_expr='icontains')

   class Meta:
      model = Observatory
      fields = ['latitude', 'longitude', 'altitude', 'project']

   @property
   def qs(self):
      parent = super(ObservatoryFilter, self).qs

      return get_allowed_objects_to_view_for_user(parent, self.request.user)


class ObservatoryViewSet(viewsets.ModelViewSet):
   queryset = Observatory.objects.all()
   serializer_class = ObservatorySerializer

   filter_backends = (DjangoFilterBackend,)
   filterset_class = ObservatoryFilter


