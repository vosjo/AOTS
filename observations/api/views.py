"""
Re-exports for observations API (implementation split across submodules).
"""

from .bulk import (
    bulkDownloadFile,
    bulkDownloadStart,
    bulkUploadLightCurves,
    bulkUploadSpectra,
    getTaskStatus,
)
from .processing import (
    getLightCurveHeader,
    getLightCurvePath,
    getRawSpecfilePath,
    getSpecfileHeader,
    getSpecfilePath,
    getSpecfileRawPath,
    processLightCurve,
    processRawSpecfile,
    processSpecfile,
    processSpectrum,
)
from .viewsets import (
    LightCurveViewSet,
    ObservatoryViewSet,
    RawSpecFileViewSet,
    SpecFileViewSet,
    SpectrumViewSet,
    UserInfoViewSet,
)

__all__ = [
    'SpectrumViewSet',
    'UserInfoViewSet',
    'SpecFileViewSet',
    'RawSpecFileViewSet',
    'LightCurveViewSet',
    'ObservatoryViewSet',
    'processSpectrum',
    'processSpecfile',
    'processRawSpecfile',
    'processLightCurve',
    'getSpecfileHeader',
    'getSpecfilePath',
    'getSpecfileRawPath',
    'getRawSpecfilePath',
    'getLightCurveHeader',
    'getLightCurvePath',
    'bulkUploadSpectra',
    'bulkUploadLightCurves',
    'bulkDownloadStart',
    'bulkDownloadFile',
    'getTaskStatus',
]
