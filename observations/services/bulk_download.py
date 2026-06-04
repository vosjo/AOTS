"""
Build bulk spectrum ZIP archives for API download.
"""

import os
import random
import shutil
import tempfile

from django.conf import settings

from AOTS.custom_permissions import get_allowed_objects_to_view_for_user
from observations.models import Spectrum


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
        qs.prefetch_related('specfile_set', 'star'),
        user,
    )


def collect_download_files(spectra_qs):
    files_to_return = []
    preferred_filenames = []
    for spec in spectra_qs:
        spfiles = list(spec.specfile_set.all())
        star_name = spec.star.name if spec.star else 'unknown'
        for i, specfile in enumerate(spfiles):
            files_to_return.append(specfile.specfile.path)
            preferred_filenames.append(f'spec_{star_name}_{i}.fits')
    return files_to_return, preferred_filenames


def build_zip_archive(files_to_return, preferred_filenames):
    """
    Copy files into a ZIP and return path to the zip file.
    Caller must delete the parent temp directory when done.
    """
    temp_directory = tempfile.mkdtemp(prefix='aots_bulk_')
    subdir = os.path.join(temp_directory, 'spec_dir')
    os.mkdir(subdir)

    for path, name in zip(files_to_return, preferred_filenames):
        shutil.copy2(path, os.path.join(subdir, name))

    zip_base = os.path.join(temp_directory, 'files')
    shutil.make_archive(zip_base, 'zip', subdir)
    return os.path.join(temp_directory, 'files.zip'), temp_directory


def bulk_download_artifact_path(task_id):
    directory = os.path.join(settings.MEDIA_ROOT, 'bulk_downloads')
    os.makedirs(directory, exist_ok=True)
    return os.path.join(directory, f'{task_id}.zip')
