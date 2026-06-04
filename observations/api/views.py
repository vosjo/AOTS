"""
Re-exports for observations API (implementation split across submodules).
"""

from .viewsets import (
    SpectrumViewSet,
    UserInfoViewSet,
    SpecFileViewSet,
    RawSpecFileViewSet,
    LightCurveViewSet,
    ObservatoryViewSet,
)
from .processing import (
    processSpectrum,
    processSpecfile,
    processRawSpecfile,
    processLightCurve,
    getSpecfileHeader,
    getSpecfilePath,
    getSpecfileRawPath,
    getRawSpecfilePath,
    getLightCurveHeader,
    getLightCurvePath,
)
from .bulk import (
    bulkUploadSpectra,
    bulkDownloadSpectra,
    bulkDownloadSpectraStart,
    bulkDownloadSpectraFile,
    getTaskStatus,
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
    'bulkDownloadSpectra',
    'bulkDownloadSpectraStart',
    'bulkDownloadSpectraFile',
    'getTaskStatus',
]
