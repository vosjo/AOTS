from astropy.io import fits
from django.core.exceptions import ObjectDoesNotExist
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response

from analysis.auxil import process_datasets
from analysis.models import Method, DataSet, Parameter
from stars.models import Project
from users.api_auth import authenticate_API_key
from .filter import DataSetFilter, MethodFilter, ParameterFilter, SEDFilter, RVcurveFilter
from .serializers import MethodSerializer, DataSetListSerializer, ParameterListSerializer, SEDSerializer, \
    RVcurveSerializer
from ..auxil.apiprocessing import find_or_create_star
from ..models.SEDs import SED
from ..models.rvcurves import RVcurve


# ===============================================================
# DataSet
# ===============================================================

class DatasetViewSet(viewsets.ModelViewSet):
    queryset = DataSet.objects.all()
    serializer_class = DataSetListSerializer

    filter_backends = (DjangoFilterBackend,)
    filterset_class = DataSetFilter


# ===============================================================
# Methods
# ===============================================================

class MethodViewSet(viewsets.ModelViewSet):
    queryset = Method.objects.all()
    serializer_class = MethodSerializer

    filter_backends = (DjangoFilterBackend,)
    filterset_class = MethodFilter


# ===============================================================
# Parameter
# ===============================================================

class ParameterViewSet(viewsets.ModelViewSet):
    queryset = Parameter.objects.all()
    serializer_class = ParameterListSerializer

    filter_backends = (DjangoFilterBackend,)
    filterset_class = ParameterFilter


@api_view(['POST'])
def processDataSet(request, pk):
    success, message = process_datasets.process_analysis_file(pk)
    dataset = DataSet.objects.get(pk=pk)

    return Response(DataSetListSerializer(dataset).data)


# New SED and RVcurve stuff

class SEDViewSet(viewsets.ModelViewSet):
    queryset = SED.objects.all()
    serializer_class = SEDSerializer

    filter_backends = (DjangoFilterBackend,)
    filterset_class = SEDFilter


class RVcurveViewSet(viewsets.ModelViewSet):
    queryset = RVcurve.objects.all()
    serializer_class = RVcurveSerializer

    filter_backends = (DjangoFilterBackend,)
    filterset_class = RVcurveFilter


@api_view(('POST',))
@authentication_classes([])
@permission_classes([])
@authenticate_API_key
def bulkUploadRVcurves(request, **kwargs):
    if request.method == "POST":
        #   Get files
        files = request.FILES.getlist('rvcurvefile')
        project_pk = request.META.get("HTTP_PROJECTID")

        if project_pk is None:
            return Response(status.HTTP_400_BAD_REQUEST)

        try:
            project = Project.objects.get(pk=int(project_pk))
        except ValueError:
            project = Project.objects.get(name__exact=project_pk)
        except ObjectDoesNotExist:
            return Response(status.HTTP_400_BAD_REQUEST)

        returned_messages = []
        n_exceptions = 0

        for f in files:
            test = fits.open(f)
            metadata = dict(test[0].header)

            newrvcurve = RVcurve(
                sourcefile=f,
                average_rv=metadata["RVAVG"],
                average_rv_err=metadata["U_RVAVG"],
                delta_rv=metadata["DRV"],
                delta_rv_err=metadata["U_DRV"],
                logp=metadata["LOGP"],
                N_samples=metadata["NSPEC"],
                time_spanned=metadata["TSPAN"],
                project=project,
            )
            newrvcurve.save()

            success, msg, star = find_or_create_star(metadata, project, newrvcurve)

            if success:
                returned_messages.append(f"Successfully added RV curve to star {star.name}")
            else:
                n_exceptions += 1
                returned_messages.append(f"Something went wrong for file {f}")

        returned_messages = ";".join(returned_messages)

        if n_exceptions != 0:
            if n_exceptions == len(files):
                return Response(status=status.HTTP_400_BAD_REQUEST, data=returned_messages)
            else:
                return Response(status=status.HTTP_207_MULTI_STATUS, data=returned_messages)

        return Response(status=status.HTTP_200_OK, data=returned_messages)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)