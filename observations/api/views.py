# from rest_framework.generics import (
# CreateAPIView,
# DestroyAPIView,
# ListAPIView,
# UpdateAPIView,
# RetrieveAPIView,
# RetrieveUpdateAPIView
# )
import os
import shutil
import tempfile
import zipfile
import random

from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist

from observations.auxil import read_spectrum, read_lightcurve
from observations.models import (
    Spectrum,
    UserInfo,
    SpecFile,
    RawSpecFile,
    LightCurve,
    Observatory,
)
from stars.models import Project
from users.models import User
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
from users.api_auth import authenticate_API_key
from rest_framework import status


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
    rawspecfile = RawSpecFile.objects.get(pk=rawspecfile_pk)

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


# ===============================================================
# API call handling
# ===============================================================


@api_view(('POST',))
@authentication_classes([])
@permission_classes([])
@authenticate_API_key
def bulkUploadSpectra(request, **kwargs):
    if request.method == "POST":
        #   Get files
        files = request.FILES.getlist('spectrumfile')
        project_pk = request.META.get("HTTP_PROJECTID")

        if project_pk is None:
            return Response(status.HTTP_400_BAD_REQUEST)

        try:
            project = Project.objects.get(pk=int(project_pk))
        except ValueError:
            project = Project.objects.get(name__exact=project_pk)
        except ObjectDoesNotExist:
            return Response(status.HTTP_400_BAD_REQUEST)

        user_info = {}

        returned_messages = []
        n_exceptions = 0

        for f in files:
            newspec = SpecFile(
                specfile=f,
                project=project,
            )
            newspec.save()

            try:
                success, message = read_spectrum.process_specfile(
                    newspec.pk,
                    create_new_star=True,
                    user_info=user_info,
                )

                newspec.refresh_from_db()
                returned_messages.append(message)

                if not success:
                    n_exceptions += 1

            except Exception as e:
                returned_messages.append(str(e))
                newspec.delete()
                n_exceptions += 1

        returned_messages = ";".join(returned_messages)

        if n_exceptions != 0:
            if n_exceptions == len(files):
                return Response(status=status.HTTP_400_BAD_REQUEST, data=returned_messages)
            else:
                return Response(status=status.HTTP_207_MULTI_STATUS, data=returned_messages)

        return Response(status=status.HTTP_200_OK, data=returned_messages)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(('GET',))
@authentication_classes([])
@permission_classes([])
@authenticate_API_key
def bulkDownloadSpectra(request, **kwargs):
    if request.method == "GET":
        project_pk = request.META.get("HTTP_PROJECTID")
        requested_stars = request.META.get("HTTP_STARIDLIST").split(";")

        if project_pk is None:
            return Response(status.HTTP_400_BAD_REQUEST)

        try:
            project = Project.objects.get(pk=int(project_pk))
        except ValueError:
            project = Project.objects.get(name__exact=project_pk)
        except ObjectDoesNotExist:
            return Response(status.HTTP_400_BAD_REQUEST)

        files_to_return = []
        preferred_filenames = []

        # Check if identifiers or pks
        list_contains_names = False
        try:
            int(requested_stars[0]) # A star name is not an integer
        except ValueError:
            list_contains_names = True

        if list_contains_names:
            spectra_to_return = Spectrum.objects.filter(project=project,
                                                        star__name__in=requested_stars).prefetch_related('specfile_set')
        else:
            spectra_to_return = Spectrum.objects.filter(project=project, pk__in=requested_stars).prefetch_related(
                'specfile_set')

        for spec in spectra_to_return:
            spfiles = list(spec.specfile_set.all())
            for i, specfile in enumerate(spfiles):
                files_to_return.append(specfile.specfile.path)
                preferred_filenames.append("spec_"+spec.star.name+f"_{i}.fits")

        # Create a temporary directory to store the files
        cwd = os.getcwd()
        temp_directory = os.path.join(cwd, f'tmp{str(random.random()).replace(".", "")}/')
        subdir = os.path.join(temp_directory, "spec_dir/")

        # Create the temporary directory and subdirectory
        os.mkdir(temp_directory)
        os.mkdir(subdir)

        # Copy the files to the temporary directory
        temp_file_paths = []
        for path, name in zip(files_to_return, preferred_filenames):
            temp_path = os.path.join(subdir, name)
            shutil.copy2(path, temp_path)
            temp_file_paths.append(temp_path)

        # Create a zip file containing the files
        zip_file_path = os.path.join(temp_directory, 'files')
        shutil.make_archive(zip_file_path, 'zip', subdir)

        with open(zip_file_path+".zip", 'rb') as archive_to_download:
            tmp = tempfile.TemporaryFile()
            tmp.write(archive_to_download.read())
            tmp.seek(0)

        # Create a response with the zip file
        response = FileResponse(tmp, as_attachment=True, filename='files.zip', status=status.HTTP_200_OK)

        # Clean up the temporary files
        shutil.rmtree(temp_directory)

        return response
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)
