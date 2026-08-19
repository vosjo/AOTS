from django.urls import include, path
from rest_framework import routers

from .plots import lightcurve_plot, spectrum_plot
from .views import (
    LightCurveViewSet,
    ObservatoryViewSet,
    RawSpecFileViewSet,
    SpecFileViewSet,
    SpectrumViewSet,
    UserInfoViewSet,
    bulkDownloadFile,
    bulkDownloadStart,
    bulkUploadLightCurves,
    bulkUploadSpectra,
    getLightCurveHeader,
    getLightCurvePath,
    getRawSpecfilePath,
    getSpecfileHeader,
    getSpecfilePath,
    getSpecfileRawPath,
    getTaskStatus,
    processLightCurve,
    processRawSpecfile,
    processSpecfile,
    processSpectrum,
)

app_name = 'observations-api'

router = routers.DefaultRouter()
router.register(r'spectra', SpectrumViewSet)
router.register(r'userinfo', UserInfoViewSet)
router.register(r'specfiles', SpecFileViewSet)
router.register(r'rawspecfiles', RawSpecFileViewSet)
router.register(r'lightcurves', LightCurveViewSet)
router.register(r'observatories', ObservatoryViewSet)

urlpatterns = [
    path('', include(router.urls)),
    #    Spectra
    path(
        'spectra/<int:spectrum_pk>/process/',
        processSpectrum,
        name='process_spectrum',
    ),
    #    SpecFiles
    path(
        'specfiles/<int:specfile_pk>/process/',
        processSpecfile,
        name='process_specfile',
    ),
    path(
        'specfiles/<int:specfile_pk>/header/',
        getSpecfileHeader,
        name='specfile_header',
    ),
    path(
        'specfiles/<int:specfile_pk>/path/',
        getSpecfilePath,
        name='specfile_path',
    ),
    path(
        'specfiles/<int:specfile_pk>/raw_path/',
        getSpecfileRawPath,
        name='specfile_rawpath',
    ),
    #    RawSpecFiles
    path(
        'rawspecfiles/<int:rawspecfile_pk>/process/',
        processRawSpecfile,
        name='process_rawspecfile',
    ),
    path(
        'rawspecfiles/<int:rawspecfile_pk>/path/',
        getRawSpecfilePath,
        name='rawspecfile_path',
    ),
    #    Lightcurves
    path(
        'lightcurves/<int:lightcurve_pk>/process/',
        processLightCurve,
        name='process_lightcurve',
    ),
    path(
        'lightcurves/<int:lightcurve_pk>/header/',
        getLightCurveHeader,
        name='lightcurve_header',
    ),
    path(
        'lightcurves/<int:lightcurve_pk>/path/',
        getLightCurvePath,
        name='lightcurve_path',
    ),
    path(
        'api-spec-upload/',
        bulkUploadSpectra,
        name='api-spec-upload',
    ),
    path(
        'api-lc-upload/',
        bulkUploadLightCurves,
        name='api-lc-upload',
    ),
    path(
        'bulk-download/start/',
        bulkDownloadStart,
        name='bulk-download-start',
    ),
    path(
        'bulk-download/<uuid:task_id>/file/',
        bulkDownloadFile,
        name='bulk-download-file',
    ),
    path(
        'tasks/<uuid:task_id>/',
        getTaskStatus,
        name='task-status',
    ),
    path('spectra/<int:pk>/plot/', spectrum_plot, name='spectrum-plot'),
    path('lightcurves/<int:pk>/plot/', lightcurve_plot, name='lightcurve-plot'),
]
