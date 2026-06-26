"""Explicit write API for Project lifecycle."""

from __future__ import annotations

from stars.models import Project


def prepare_project_deletion(project: Project) -> None:
    """
    Delete observation rows that reference observatories with PROTECT.

    Project CASCADE would remove observatories while light curves / spectra /
    upload metadata still point at them, which raises ProtectedError.
    """
    from observations.models import LightCurve, Spectrum, UserInfo

    LightCurve.objects.filter(project=project).delete()
    UserInfo.objects.filter(project=project).delete()
    Spectrum.objects.filter(project=project).delete()


def delete_project(project: Project) -> None:
    prepare_project_deletion(project)
    project.delete()
