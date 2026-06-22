"""Starmap coordinate helpers and metadata for the interactive Bokeh dashboard map."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from astropy import units as u
from astropy.coordinates import Galactic, SkyCoord

from analysis.services.parameter_consensus import get_consensus_parameter

mpl.use('Agg')


@dataclass(frozen=True)
class StarPosition:
    star_pk: int
    name: str
    ra_deg: float
    dec_deg: float
    parallax_mas: float | None
    galactic_l_deg: float
    galactic_b_deg: float
    distance_kpc: float | None


def marker_size(nstars: int) -> float:
    if nstars < 100:
        return 10.0
    if nstars < 50000:
        return -0.00018 * nstars + 10.018
    return 1.0


@dataclass(frozen=True)
class AitoffGrid:
    meridian_xs: list[list[float]]
    meridian_ys: list[list[float]]
    parallel_xs: list[list[float]]
    parallel_ys: list[list[float]]
    outline_xs: list[float]
    outline_ys: list[float]
    longitude_tick_labels: list[dict[str, float | str]]
    latitude_tick_labels: list[dict[str, float | str]]


_AITOFF_AX = None


def _get_aitoff_transform():
    """Reuse one matplotlib Aitoff axes for all coordinate transforms."""
    global _AITOFF_AX
    if _AITOFF_AX is None:
        _, _AITOFF_AX = plt.subplots(subplot_kw={'projection': 'aitoff'}, figsize=(2, 1))
    return _AITOFF_AX.transProjection


def galactic_aitoff_xy(l_deg: np.ndarray | float, b_deg: np.ndarray | float) -> tuple[np.ndarray, np.ndarray]:
    """Project galactic l,b (degrees) to Aitoff x,y (matplotlib projection plane)."""
    l = np.atleast_1d(np.asarray(l_deg, dtype=float))
    b = np.atleast_1d(np.asarray(b_deg, dtype=float))
    lon = -np.deg2rad(l)
    lon = (lon + np.pi) % (2 * np.pi) - np.pi
    lat = np.deg2rad(b)
    xy = _get_aitoff_transform().transform(np.column_stack([lon, lat]))
    return xy[:, 0], xy[:, 1]


def _aitoff_outline_xy(*, lat_samples: int = 181) -> tuple[list[float], list[float]]:
    """Closed path of the Aitoff map rim in projected coordinates."""
    latitudes = np.linspace(-89.9, 89.9, lat_samples)
    l_right = np.linspace(181, 359, 361)
    l_left = np.linspace(0, 179, 361)

    right_l = np.broadcast_to(l_right, (lat_samples, l_right.size))
    right_b = np.broadcast_to(latitudes[:, None], (lat_samples, l_right.size))
    x_right, y_right = galactic_aitoff_xy(right_l.ravel(), right_b.ravel())
    x_right = x_right.reshape(lat_samples, l_right.size)
    y_right = y_right.reshape(lat_samples, l_right.size)
    right_idx = np.argmax(x_right, axis=1)
    row_idx = np.arange(lat_samples)

    left_l = np.broadcast_to(l_left, (lat_samples, l_left.size))
    left_b = np.broadcast_to(latitudes[::-1][:, None], (lat_samples, l_left.size))
    x_left, y_left = galactic_aitoff_xy(left_l.ravel(), left_b.ravel())
    x_left = x_left.reshape(lat_samples, l_left.size)
    y_left = y_left.reshape(lat_samples, l_left.size)
    left_idx = np.argmin(x_left, axis=1)

    outline_x = x_right[row_idx, right_idx].tolist()
    outline_y = y_right[row_idx, right_idx].tolist()
    outline_x.extend(x_left[row_idx, left_idx].tolist())
    outline_y.extend(y_left[row_idx, left_idx].tolist())
    if outline_x:
        outline_x.append(outline_x[0])
        outline_y.append(outline_y[0])
    return outline_x, outline_y


def _parallel_segments() -> tuple[np.ndarray, np.ndarray]:
    """Longitude samples for one parallel without crossing the l=180 discontinuity."""
    return np.linspace(0, 179, 180), np.linspace(181, 359, 179)


@lru_cache(maxsize=4)
def build_aitoff_grid(*, lon_step: int = 30, lat_step: int = 30) -> AitoffGrid:
    """Grid lines and degree tick labels for the interactive Aitoff starmap."""
    meridian_xs: list[list[float]] = []
    meridian_ys: list[list[float]] = []
    b_line = np.linspace(-89.9, 89.9, 360)
    for lon in np.arange(0, 360, lon_step):
        x, y = galactic_aitoff_xy(np.full_like(b_line, lon), b_line)
        meridian_xs.append(x.tolist())
        meridian_ys.append(y.tolist())

    parallel_xs: list[list[float]] = []
    parallel_ys: list[list[float]] = []
    latitudes = np.arange(-90 + lat_step, 90, lat_step)
    lon_left, lon_right = _parallel_segments()
    # Avoid l=180 in parallels: projection jumps from left rim (l=180) to right rim (l=181).
    for lat in latitudes:
        for lon in (lon_left, lon_right):
            x, y = galactic_aitoff_xy(lon, np.full_like(lon, lat))
            parallel_xs.append(x.tolist())
            parallel_ys.append(y.tolist())

    outline_x, outline_y = _aitoff_outline_xy()

    longitude_tick_labels: list[dict[str, float | str]] = []
    for lon in np.arange(0, 360, lon_step):
        x, y = galactic_aitoff_xy([lon], [0.0])
        longitude_tick_labels.append({
            'x': float(x[0]),
            'y': float(y[0]),
            'text': f'{int(lon)}°',
        })

    latitude_tick_labels: list[dict[str, float | str]] = []
    for lat in latitudes:
        x, y = galactic_aitoff_xy([0.0], [lat])
        latitude_tick_labels.append({
            'x': float(x[0]),
            'y': float(y[0]),
            'text': f'{int(lat)}°',
        })

    return AitoffGrid(
        meridian_xs=meridian_xs,
        meridian_ys=meridian_ys,
        parallel_xs=parallel_xs,
        parallel_ys=parallel_ys,
        outline_xs=outline_x,
        outline_ys=outline_y,
        longitude_tick_labels=longitude_tick_labels,
        latitude_tick_labels=latitude_tick_labels,
    )


def collect_star_positions(project) -> list[StarPosition]:
    positions: list[StarPosition] = []
    for star in project.star_set.all().order_by('pk'):
        if star.ra is None or star.dec is None:
            continue
        consensus = get_consensus_parameter(star, 'parallax', 0)
        parallax_mas = None
        distance_kpc = None
        if consensus is not None and consensus.value is not None and consensus.value > 0:
            parallax_mas = float(consensus.value)
            distance_kpc = float(
                (parallax_mas * u.mas).to_value(u.kpc, equivalencies=u.parallax()),
            )
        galactic = SkyCoord(
            ra=star.ra * u.deg,
            dec=star.dec * u.deg,
            frame='icrs',
        ).transform_to(Galactic())
        positions.append(
            StarPosition(
                star_pk=star.pk,
                name=star.name,
                ra_deg=float(star.ra),
                dec_deg=float(star.dec),
                parallax_mas=parallax_mas,
                galactic_l_deg=float(galactic.l.deg),
                galactic_b_deg=float(galactic.b.deg),
                distance_kpc=distance_kpc,
            ),
        )
    return positions


def starmap_star_records(project, *, project_slug: str | None = None) -> list[dict[str, Any]]:
    slug = project_slug or project.slug
    records: list[dict[str, Any]] = []
    for position in collect_star_positions(project):
        records.append({
            'pk': position.star_pk,
            'name': position.name,
            'ra': position.ra_deg,
            'dec': position.dec_deg,
            'l': position.galactic_l_deg,
            'b': position.galactic_b_deg,
            'parallax_mas': position.parallax_mas,
            'distance_kpc': position.distance_kpc,
            'url': f'/w/{slug}/systems/stars/{position.star_pk}/',
        })
    return records


def starmap_metadata(project) -> dict[str, Any]:
    positions = collect_star_positions(project)
    colored_by_distance = any(p.parallax_mas is not None and p.parallax_mas > 0 for p in positions)
    return {
        'n_stars': len(positions),
        'colored_by_distance': colored_by_distance,
    }
