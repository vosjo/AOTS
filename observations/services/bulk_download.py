"""
Build bulk spectrum ZIP archives for API download.
"""

import os
import shutil
import tempfile
import time

from django.conf import settings
from django.utils import timezone

from AOTS.custom_permissions import get_allowed_objects_to_view_for_user
from analysis.models import Analysis
from observations.models import LightCurve, RawSpecFile, Spectrum

BULK_DOWNLOAD_KINDS = frozenset({
    'processed',
    'raw',
    'rawspecfiles',
    'lightcurves',
    'analyses',
})

BULK_DOWNLOAD_FILENAME_PREFIX = {
    'processed': 'spectra',
    'raw': 'raw_spectra',
    'rawspecfiles': 'raw_files',
    'lightcurves': 'lightcurves',
    'analyses': 'analyses',
}


def bulk_download_filename(kind, at=None):
    """Return a download filename like spectra_20260523_143052.zip."""
    prefix = BULK_DOWNLOAD_FILENAME_PREFIX.get(kind, 'download')
    moment = at or timezone.now()
    stamp = moment.strftime('%Y%m%d_%H%M%S')
    return f'{prefix}_{stamp}.zip'


def bulk_download_directory():
    directory = os.path.join(settings.MEDIA_ROOT, 'bulk_downloads')
    os.makedirs(directory, exist_ok=True)
    return directory


def bulk_download_artifact_path(task_id):
    return os.path.join(bulk_download_directory(), f'{task_id}.zip')


def resolve_spectra_queryset(project, requested_stars, user):
    if not requested_stars:
        return Spectrum.objects.none()

    list_contains_names = False
    try:
        int(requested_stars[0])
    except (ValueError, IndexError):
        list_contains_names = True

    if list_contains_names:
        qs = Spectrum.objects.filter(
            project=project,
            star__name__in=requested_stars,
        )
    else:
        qs = Spectrum.objects.filter(
            project=project,
            pk__in=requested_stars,
        )

    return get_allowed_objects_to_view_for_user(
        qs.prefetch_related('specfile_set__rawspecfile_set', 'star'),
        user,
    )


def resolve_rawspecfiles_queryset(project, requested_ids, user):
    if not requested_ids:
        return RawSpecFile.objects.none()

    qs = RawSpecFile.objects.filter(
        project=project,
        pk__in=requested_ids,
    )
    return get_allowed_objects_to_view_for_user(qs, user)


def collect_processed_download_entries(spectra_qs):
    entries = []
    for spec in spectra_qs:
        star_name = spec.star.name if spec.star else 'unknown'
        for i, specfile in enumerate(spec.specfile_set.all()):
            entries.append((
                specfile.specfile.path,
                f'spec_{star_name}_{i}.fits',
            ))
    return entries


def collect_raw_spectra_download_entries(spectra_qs):
    entries = []
    for spec in spectra_qs:
        star_name = (spec.star.name if spec.star else 'unknown').strip().replace(' ', '_')
        for specfile in spec.specfile_set.all():
            hjd = specfile.hjd
            for raw in specfile.rawspecfile_set.all():
                basename = os.path.basename(raw.rawfile.name)
                entries.append((
                    raw.rawfile.path,
                    f'{star_name}/{hjd}/{basename}',
                ))
    return entries


def collect_rawspecfile_download_entries(rawspecfile_qs):
    entries = []
    for raw in rawspecfile_qs:
        basename = os.path.basename(raw.rawfile.name)
        entries.append((raw.rawfile.path, basename))
    return entries


def resolve_lightcurves_queryset(project, requested_ids, user):
    if not requested_ids:
        return LightCurve.objects.none()

    qs = LightCurve.objects.filter(
        project=project,
        pk__in=requested_ids,
    )
    return get_allowed_objects_to_view_for_user(qs, user)


def resolve_analyses_queryset(project, requested_ids, user):
    if not requested_ids:
        return Analysis.objects.none()

    qs = Analysis.objects.filter(
        project=project,
        pk__in=requested_ids,
    )
    return get_allowed_objects_to_view_for_user(qs, user)


def collect_lightcurve_download_entries(lightcurve_qs):
    entries = []
    for lc in lightcurve_qs:
        basename = os.path.basename(lc.lcfile.name)
        entries.append((lc.lcfile.path, basename))
    return entries


def collect_analysis_download_entries(analysis_qs):
    entries = []
    for analysis in analysis_qs:
        basename = os.path.basename(analysis.datafile.name)
        entries.append((analysis.datafile.path, basename))
    return entries


def collect_download_entries(project, requested_ids, user, kind):
    if kind == 'rawspecfiles':
        rawspecfiles = resolve_rawspecfiles_queryset(project, requested_ids, user)
        return collect_rawspecfile_download_entries(rawspecfiles)
    if kind == 'lightcurves':
        lightcurves = resolve_lightcurves_queryset(project, requested_ids, user)
        return collect_lightcurve_download_entries(lightcurves)
    if kind == 'analyses':
        analyses = resolve_analyses_queryset(project, requested_ids, user)
        return collect_analysis_download_entries(analyses)

    spectra = resolve_spectra_queryset(project, requested_ids, user)
    if kind == 'raw':
        return collect_raw_spectra_download_entries(spectra)
    return collect_processed_download_entries(spectra)


def build_zip_archive(file_entries):
    """
    Copy files into a ZIP and return path to the zip file.
    file_entries: iterable of (source_path, arcname_within_zip).
    Caller must delete the parent temp directory when done.
    """
    temp_directory = tempfile.mkdtemp(prefix='aots_bulk_')
    subdir = os.path.join(temp_directory, 'spec_dir')
    os.makedirs(subdir, exist_ok=True)

    for source_path, arcname in file_entries:
        dest = os.path.join(subdir, arcname)
        parent = os.path.dirname(dest)
        if parent:
            os.makedirs(parent, exist_ok=True)
        shutil.copy2(source_path, dest)

    zip_base = os.path.join(temp_directory, 'files')
    shutil.make_archive(zip_base, 'zip', subdir)
    return os.path.join(temp_directory, 'files.zip'), temp_directory


def cleanup_expired_bulk_downloads():
    """
    Remove ZIP files older than BULK_DOWNLOAD_TTL_SECONDS.
    Returns the number of deleted files.
    """
    ttl = getattr(settings, 'BULK_DOWNLOAD_TTL_SECONDS', 86400)
    directory = bulk_download_directory()
    if not os.path.isdir(directory):
        return 0

    cutoff = time.time() - ttl
    removed = 0
    for name in os.listdir(directory):
        if not name.endswith('.zip'):
            continue
        path = os.path.join(directory, name)
        try:
            if os.path.isfile(path) and os.path.getmtime(path) < cutoff:
                os.unlink(path)
                removed += 1
        except OSError:
            continue
    return removed


def remove_bulk_download_artifact(task_id):
    path = bulk_download_artifact_path(task_id)
    if os.path.isfile(path):
        os.unlink(path)
        return True
    return False


class BulkDownloadFile:
    """File wrapper that removes the artifact when the response is closed."""

    def __init__(self, task_id, download_filename='files.zip'):
        self.task_id = task_id
        self.name = download_filename
        self.path = bulk_download_artifact_path(task_id)
        self._file = open(self.path, 'rb')

    def read(self, size=-1):
        return self._file.read(size)

    def close(self):
        self._file.close()
        if getattr(settings, 'BULK_DOWNLOAD_DELETE_AFTER_SEND', True):
            remove_bulk_download_artifact(self.task_id)

    def __iter__(self):
        return self

    def __next__(self):
        chunk = self.read(8192)
        if not chunk:
            raise StopIteration
        return chunk
