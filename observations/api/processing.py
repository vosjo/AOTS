from rest_framework.decorators import api_view
from rest_framework.response import Response

from AOTS.api_processing import run_process_view
from AOTS.permissions_helpers import get_object_if_allowed
from observations.models import Spectrum, SpecFile, RawSpecFile, LightCurve
from observations.services import fits_io
from observations.tasks import (
    process_lightcurve_task,
    process_raw_specfile_task,
    process_specfile_task,
    process_spectrum_task,
)
from .serializers import (
    SpectrumSerializer,
    SpecFileSerializer,
    RawSpecFileSerializer,
    LightCurveSerializer,
)


@api_view(['POST'])
def processSpectrum(request, spectrum_pk):
    spectrum = get_object_if_allowed(
        Spectrum, request, spectrum_pk, require_edit=True,
    )
    return run_process_view(
        request, spectrum, process_spectrum_task, SpectrumSerializer,
    )


@api_view(['POST'])
def processSpecfile(request, specfile_pk):
    specfile = get_object_if_allowed(
        SpecFile, request, specfile_pk, require_edit=True,
    )
    return run_process_view(
        request, specfile, process_specfile_task, SpecFileSerializer,
    )


@api_view(['GET'])
def getSpecfileHeader(request, specfile_pk):
    specfile = get_object_if_allowed(SpecFile, request, specfile_pk)
    return Response(fits_io.read_specfile_header(specfile))


@api_view(['GET'])
def getSpecfilePath(request, specfile_pk):
    from AOTS.media_signing import signed_filefield_url
    specfile = get_object_if_allowed(SpecFile, request, specfile_pk)
    return Response(signed_filefield_url(specfile.specfile, original_name=specfile.original_name))


@api_view(['GET'])
def getSpecfileRawPath(request, specfile_pk):
    from AOTS.media_signing import signed_filefield_url
    specfile = get_object_if_allowed(SpecFile, request, specfile_pk)
    path_list = [
        signed_filefield_url(raw.rawfile, original_name=raw.original_name)
        for raw in specfile.rawspecfile_set.all()
    ]
    return Response(path_list)


@api_view(['POST'])
def processRawSpecfile(request, rawspecfile_pk):
    rawspecfile = get_object_if_allowed(
        RawSpecFile, request, rawspecfile_pk, require_edit=True,
    )
    return run_process_view(
        request, rawspecfile, process_raw_specfile_task, RawSpecFileSerializer,
    )


@api_view(['GET'])
def getRawSpecfilePath(request, rawspecfile_pk):
    from AOTS.media_signing import signed_filefield_url
    rawfile = get_object_if_allowed(RawSpecFile, request, rawspecfile_pk)
    return Response(signed_filefield_url(rawfile.rawfile, original_name=rawfile.original_name))


@api_view(['POST'])
def processLightCurve(request, lightcurve_pk):
    lightcurve = get_object_if_allowed(
        LightCurve, request, lightcurve_pk, require_edit=True,
    )
    return run_process_view(
        request, lightcurve, process_lightcurve_task, LightCurveSerializer,
    )


@api_view(['GET'])
def getLightCurveHeader(request, lightcurve_pk):
    lightcurve = get_object_if_allowed(LightCurve, request, lightcurve_pk)
    return Response(fits_io.read_lightcurve_header(lightcurve))


@api_view(['GET'])
def getLightCurvePath(request, lightcurve_pk):
    from AOTS.media_signing import signed_filefield_url
    lightcurve = get_object_if_allowed(LightCurve, request, lightcurve_pk)
    return Response(signed_filefield_url(lightcurve.lcfile, original_name=lightcurve.original_name))
