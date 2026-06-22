"""Generate project starmap PNG previews stored on Project FileFields."""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from typing import Any

import astropy.coordinates as coord
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from astropy import units as u
from astropy.coordinates import Galactic, SkyCoord
from django.core.cache import cache
from django.core.exceptions import SuspiciousFileOperation
from django.core.files.base import ContentFile
from django.utils import timezone

from analysis.services.parameter_consensus import get_consensus_parameter

logger = logging.getLogger('AOTS.starmap')

STARMAP_REGEN_CACHE_PREFIX = 'starmap_regen:'
STARMAP_REGEN_CACHE_TTL = 300
STARMAP_REGEN_COUNTDOWN = 120

mpl.use('Agg')


@dataclass(frozen=True)
class StarPosition:
    ra_deg: float
    dec_deg: float
    parallax_mas: float | None


@dataclass(frozen=True)
class StarmapResult:
    preview_url: str | None
    full_url: str | None
    generated_at: str | None
    n_stars: int
    colored_by_distance: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            'preview_url': self.preview_url,
            'full_url': self.full_url,
            'generated_at': self.generated_at,
            'n_stars': self.n_stars,
            'colored_by_distance': self.colored_by_distance,
        }


def marker_size(nstars: int) -> float:
    if nstars < 100:
        return 10.0
    if nstars < 50000:
        return -0.00018 * nstars + 10.018
    return 1.0


def collect_star_positions(project) -> list[StarPosition]:
    positions: list[StarPosition] = []
    for star in project.star_set.all().order_by('pk'):
        if star.ra is None or star.dec is None:
            continue
        consensus = get_consensus_parameter(star, 'parallax', 0)
        parallax_mas = None
        if consensus is not None and consensus.value is not None and consensus.value > 0:
            parallax_mas = float(consensus.value)
        positions.append(
            StarPosition(
                ra_deg=float(star.ra),
                dec_deg=float(star.dec),
                parallax_mas=parallax_mas,
            ),
        )
    return positions


def _build_skycoords(positions: list[StarPosition]) -> tuple[SkyCoord, bool]:
    ra = np.array([p.ra_deg for p in positions]) * u.deg
    dec = np.array([p.dec_deg for p in positions]) * u.deg
    parallax_mas = np.array([
        p.parallax_mas if p.parallax_mas is not None else np.nan
        for p in positions
    ])

    has_parallax = np.any(np.isfinite(parallax_mas) & (parallax_mas > 0))
    if has_parallax:
        plx = np.where(
            np.isfinite(parallax_mas) & (parallax_mas > 0),
            parallax_mas,
            np.nan,
        ) * u.mas
        distance = plx.to(u.kpc, equivalencies=u.parallax())
        distance_kpc = distance.to_value(u.kpc)
        sky = SkyCoord(ra=ra, dec=dec, distance=distance_kpc * u.kpc, frame='icrs')
        return sky.transform_to(Galactic()), True

    sky = SkyCoord(ra=ra, dec=dec, frame='icrs')
    return sky.transform_to(Galactic()), False


def _coordinates_aitoff_plot(coords: SkyCoord, *, colored_by_distance: bool):
    fig, ax = plt.subplots(
        figsize=(10, 5),
        subplot_kw={'projection': 'aitoff'},
    )

    sph = coords.spherical
    marker = marker_size(len(coords))
    lon = -sph.lon.wrap_at(180 * u.deg).radian
    lat = sph.lat.radian

    colorbar = None
    if colored_by_distance:
        distances = sph.distance.to_value(u.kpc)
        distances[~np.isfinite(distances) | (distances <= 0)] = np.nan
        scatter = ax.scatter(
            lon,
            lat,
            c=distances,
            s=marker,
            norm=mpl.colors.LogNorm(),
        )
        colorbar = fig.colorbar(scatter)
        colorbar.set_label(f'Distance [{sph.distance.unit.to_string()}]')
    else:
        ax.scatter(lon, lat, c='steelblue', s=marker)

    def fmt_func(x, _pos):
        val = coord.Angle(-x * u.radian).wrap_at(360 * u.deg).degree
        return f'${val:.0f}' + r'^{\circ}$'

    ax.xaxis.set_major_formatter(mpl.ticker.FuncFormatter(fmt_func))
    ax.grid()
    ax.set_xlabel('Galactic longitude [deg]')
    ax.set_ylabel('Galactic latitude [deg]')
    return fig, ax, colorbar


def _figure_to_png_bytes(fig, *, dpi: int) -> bytes:
    buffer = io.BytesIO()
    fig.savefig(buffer, bbox_inches='tight', format='png', dpi=dpi)
    plt.close(fig)
    buffer.seek(0)
    return buffer.read()


def _strip_preview_axes(fig, ax, colorbar) -> bytes:
    ax.xaxis.set_tick_params(labelbottom=False)
    ax.yaxis.set_tick_params(labelleft=False)
    ax.grid(True)
    for axis in (ax.xaxis, ax.yaxis):
        for tick in axis.get_major_ticks():
            tick.tick1line.set_visible(False)
            tick.tick2line.set_visible(False)
            tick.label1.set_visible(False)
            tick.label2.set_visible(False)
    ax.xaxis.label.set_visible(False)
    ax.yaxis.label.set_visible(False)
    if colorbar is not None:
        colorbar.remove()
    return _figure_to_png_bytes(fig, dpi=100)


def _delete_file_field(field) -> None:
    if not field or not field.name:
        return
    try:
        field.delete(save=False)
    except SuspiciousFileOperation:
        # Legacy starmaps from plot_star_positions.py pointed at static/, not media/.
        logger.info(
            'Legacy starmap path outside media storage, clearing reference: %s',
            field.name,
        )
        field.name = ''


def generate_starmap(project, *, user=None) -> StarmapResult:
    """Build preview/full PNGs and persist them on ``project``."""
    del user  # reserved for future history attribution
    positions = collect_star_positions(project)
    n_stars = len(positions)

    if n_stars == 0:
        _delete_file_field(project.preview_starmap)
        _delete_file_field(project.full_starmap)
        project.preview_starmap = None
        project.full_starmap = None
        project.starmap_generated_at = timezone.now()
        project.save(update_fields=['preview_starmap', 'full_starmap', 'starmap_generated_at'])
        return StarmapResult(
            preview_url=None,
            full_url=None,
            generated_at=project.starmap_generated_at.isoformat(),
            n_stars=0,
            colored_by_distance=False,
        )

    coords, colored_by_distance = _build_skycoords(positions)
    fig, ax, colorbar = _coordinates_aitoff_plot(coords, colored_by_distance=colored_by_distance)
    full_bytes = _figure_to_png_bytes(fig, dpi=300)

    fig, ax, colorbar = _coordinates_aitoff_plot(coords, colored_by_distance=colored_by_distance)
    preview_bytes = _strip_preview_axes(fig, ax, colorbar)

    preview_name = f'{project.slug}_preview.png'
    full_name = f'{project.slug}_full.png'

    _delete_file_field(project.preview_starmap)
    _delete_file_field(project.full_starmap)

    project.preview_starmap.save(preview_name, ContentFile(preview_bytes), save=False)
    project.full_starmap.save(full_name, ContentFile(full_bytes), save=False)
    project.starmap_generated_at = timezone.now()
    project.save(update_fields=['preview_starmap', 'full_starmap', 'starmap_generated_at'])

    return StarmapResult(
        preview_url=project.preview_starmap.url,
        full_url=project.full_starmap.url,
        generated_at=project.starmap_generated_at.isoformat(),
        n_stars=n_stars,
        colored_by_distance=colored_by_distance,
    )


def starmap_metadata(project, *, can_edit: bool = False) -> dict[str, Any]:
    positions = collect_star_positions(project)
    colored_by_distance = any(p.parallax_mas is not None and p.parallax_mas > 0 for p in positions)
    result = StarmapResult(
        preview_url=project.preview_starmap.url if project.preview_starmap else None,
        full_url=project.full_starmap.url if project.full_starmap else None,
        generated_at=(
            project.starmap_generated_at.isoformat()
            if project.starmap_generated_at
            else None
        ),
        n_stars=len(positions),
        colored_by_distance=colored_by_distance,
    )
    payload = result.as_dict()
    payload['can_edit'] = can_edit
    return payload


def regenerate_all_starmaps(*, project_queryset=None) -> dict[str, Any]:
    from stars.models import Project

    queryset = project_queryset if project_queryset is not None else Project.objects.all()
    summary = {
        'total': 0,
        'ok': 0,
        'failed': 0,
        'errors': [],
    }

    for project in queryset.order_by('pk'):
        if not project.star_set.exists():
            continue
        summary['total'] += 1
        try:
            generate_starmap(project)
            summary['ok'] += 1
        except Exception as exc:
            logger.exception('Starmap generation failed for project pk=%s', project.pk)
            summary['failed'] += 1
            summary['errors'].append({
                'project_pk': project.pk,
                'project_slug': project.slug,
                'message': str(exc),
            })

    return summary


def schedule_starmap_regeneration(project_pk: int, *, countdown: int = STARMAP_REGEN_COUNTDOWN) -> bool:
    """Enqueue a debounced starmap regeneration for one project."""
    from stars.tasks import regenerate_starmap_task

    cache_key = f'{STARMAP_REGEN_CACHE_PREFIX}{project_pk}'
    if cache.get(cache_key):
        return False

    cache.set(cache_key, True, STARMAP_REGEN_CACHE_TTL)
    regenerate_starmap_task.apply_async(args=[project_pk], countdown=countdown)
    return True
