# from rest_framework.generics import (
# CreateAPIView,
# DestroyAPIView,
# ListAPIView,
# UpdateAPIView,
# RetrieveAPIView,
# RetrieveUpdateAPIView
# )

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from observations.auxil import read_spectrum, read_lightcurve
from observations.models import (
    Spectrum,
    UserInfo,
    SpecFile,
    RawSpecFile,
    LightCurve,
    Observatory,
)
from .filter import (
    SpectrumFilter,
    UserInfoFilter,
    SpecFileFilter,
    RawSpecFileFilter,
    LightCurveFilter,
    ObservatoryFilter,
)
from .serializers import (
    SpectrumSerializer,
    UserInfoSerializer,
    RawSpecFileSerializer,
    SpecFileSerializer,
    LightCurveSerializer,
    ObservatorySerializer,
)


# from django_filters import rest_framework as filters


# from AOTS.custom_permissions import get_allowed_objects_to_view_for_user


# ===============================================================
# Spectrum
# ===============================================================

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


class UserInfoViewSet(viewsets.ModelViewSet):
    queryset = UserInfo.objects.all()
    serializer_class = UserInfoSerializer

    filter_backends = (DjangoFilterBackend,)
    filterset_class = UserInfoFilter


# ===============================================================
# SpecFile
# ===============================================================

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


@api_view(['GET'])
def getSpecfilePath(request, specfile_pk):
    specfile = SpecFile.objects.get(pk=specfile_pk)
    path = specfile.specfile.url

    return Response(path)


@api_view(['GET'])
def getSpecfileRawPath(request, specfile_pk):
    path_list = []
    specfile = SpecFile.objects.get(pk=specfile_pk)
    rawfiles = specfile.rawspecfile_set.all()
    for raw in rawfiles:
        path_list.append(raw.rawfile.url)

    return Response(path_list)


# ===============================================================
# RawSpecFile
# ===============================================================

class RawSpecFileViewSet(viewsets.ModelViewSet):
    queryset = RawSpecFile.objects.all()
    serializer_class = RawSpecFileSerializer

    filter_backends = (DjangoFilterBackend,)
    filterset_class = RawSpecFileFilter


@api_view(['POST'])
def processRawSpecfile(request, rawspecfile_pk):
    success, message = read_spectrum.process_raw_spec(rawspecfile_pk)
    specfile = RawSpecFile.objects.get(pk=rawspecfile_pk)

    return Response(RawSpecFileSerializer(rawspecfile).data)


@api_view(['GET'])
def getRawSpecfilePath(request, rawspecfile_pk):
    rawfile = RawSpecFile.objects.get(pk=rawspecfile_pk)
    path = rawfile.rawfile.url

    return Response(path)


# ===============================================================
# LightCurve
# ===============================================================

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


@api_view(['GET'])
def getLightCurvePath(request, lightcurve_pk):
    lightcurve = LightCurve.objects.get(pk=lightcurve_pk)
    path = lightcurve.lcfile.url

    return Response(path)


# ===============================================================
# Observatory
# ===============================================================

class ObservatoryViewSet(viewsets.ModelViewSet):
    queryset = Observatory.objects.all()
    serializer_class = ObservatorySerializer

    filter_backends = (DjangoFilterBackend,)
    filterset_class = ObservatoryFilter
