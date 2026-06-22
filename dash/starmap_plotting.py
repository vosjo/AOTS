"""Interactive Bokeh starmap (Aitoff projection via pre-transformed coordinates)."""

from __future__ import annotations

import math

import numpy as np
from bokeh.models import ColorBar, ColumnDataSource, Label, LogColorMapper, OpenURL, Range1d, TapTool
from bokeh.plotting import figure
from bokeh.transform import linear_cmap

from dash.bokeh_theme import BokehPlotTheme, apply_bokeh_figure_theme, resolve_bokeh_theme, styled_color_bar, themed_hover_tool
from stars.services.starmap import (
    AitoffGrid,
    build_aitoff_grid,
    collect_star_positions,
    galactic_aitoff_xy,
    marker_size,
)

_LABEL_BASE = {
    'text_font_size': '10px',
    'text_align': 'center',
    'text_baseline': 'middle',
}
_AXIS_TITLE_BASE = {
    'text_font_size': '11px',
    'text_align': 'center',
    'text_baseline': 'middle',
}


def _styled_color_bar(color_mapper, *, theme: BokehPlotTheme) -> ColorBar:
    return styled_color_bar(color_mapper, theme=theme, title='Distance [kpc]')


def _add_aitoff_grid_and_labels(
    p,
    *,
    grid: AitoffGrid,
    plot_x_min: float,
    plot_x_max: float,
    plot_y_min: float,
    plot_y_max: float,
    theme: BokehPlotTheme,
) -> None:
    grid_style = {
        'line_color': theme.grid_line,
        'line_alpha': theme.grid_line_alpha,
        'line_width': 0.8,
    }
    p.multi_line(grid.meridian_xs, grid.meridian_ys, **grid_style)
    p.multi_line(grid.parallel_xs, grid.parallel_ys, **grid_style)
    p.line(
        grid.outline_xs,
        grid.outline_ys,
        line_color=theme.outline,
        line_alpha=min(theme.grid_line_alpha + 0.18, 0.72),
        line_width=grid_style['line_width'],
    )

    plot_w = plot_x_max - plot_x_min
    plot_h = plot_y_max - plot_y_min
    # Degree ticks follow grid intersections (equator / l=0 meridian), like the original layout.
    tick_y_offset = plot_h * 0.06
    tick_x_offset = plot_w * 0.05
    title_y_offset = plot_h * 0.038
    title_x_offset = plot_w * 0.034
    tick_style = {**_LABEL_BASE, 'text_color': theme.tick_text}
    axis_title_style = {**_AXIS_TITLE_BASE, 'text_color': theme.axis_title}

    for tick in grid.longitude_tick_labels:
        p.add_layout(Label(
            x=tick['x'],
            y=tick['y'] - tick_y_offset,
            text=str(tick['text']),
            **tick_style,
        ))
    for tick in grid.latitude_tick_labels:
        p.add_layout(Label(
            x=tick['x'] - tick_x_offset,
            y=tick['y'],
            text=str(tick['text']),
            **tick_style,
        ))

    p.add_layout(Label(
        x=(plot_x_min + plot_x_max) / 2,
        y=plot_y_min - title_y_offset,
        text='Galactic longitude [deg]',
        **axis_title_style,
    ))
    p.add_layout(Label(
        x=plot_x_min - title_x_offset,
        y=(plot_y_min + plot_y_max) / 2,
        text='Galactic latitude [deg]',
        angle=math.pi / 2,
        **axis_title_style,
    ))


def _distance_color_mapper(distances_kpc: np.ndarray) -> LogColorMapper | None:
    positive = distances_kpc[np.isfinite(distances_kpc) & (distances_kpc > 0)]
    if positive.size == 0:
        return None
    return LogColorMapper(
        palette='Viridis256',
        low=max(float(positive.min()), 1e-6),
        high=float(positive.max()),
    )


def plot_interactive_starmap(project, *, theme: str | None = None):
    """
    Bokeh scatter in Aitoff plane (galactic coordinates).

    Bokeh has no native sky projection; x/y are computed with the same transform
    as matplotlib's ``projection='aitoff'``. Grid and degree labels are drawn
    explicitly to match the static matplotlib starmap styling.
    """
    plot_theme = resolve_bokeh_theme(theme)
    positions = collect_star_positions(project)
    if not positions:
        return None

    l_deg = np.array([p.galactic_l_deg for p in positions])
    b_deg = np.array([p.galactic_b_deg for p in positions])
    x, y = galactic_aitoff_xy(l_deg, b_deg)

    names = [p.name for p in positions]
    ra = [p.ra_deg for p in positions]
    dec = [p.dec_deg for p in positions]
    distances = np.array([
        p.distance_kpc if p.distance_kpc is not None else float('nan')
        for p in positions
    ])
    urls = [f'/w/{project.slug}/systems/stars/{p.star_pk}/' for p in positions]

    colored_by_distance = np.any(np.isfinite(distances) & (distances > 0))
    size = marker_size(len(positions))

    grid = build_aitoff_grid()
    grid_x = (
        [value for line in grid.meridian_xs + grid.parallel_xs for value in line]
        + grid.outline_xs
    )
    grid_y = (
        [value for line in grid.meridian_ys + grid.parallel_ys for value in line]
        + grid.outline_ys
    )
    x_min = min(grid_x + x.tolist())
    x_max = max(grid_x + x.tolist())
    y_min = min(grid_y + y.tolist())
    y_max = max(grid_y + y.tolist())
    plot_w = x_max - x_min
    plot_h = y_max - y_min
    # Outline sampling slightly undershoots the true Aitoff rim on the right; pad asymmetrically.
    x_pad_left = max(plot_w * 0.055, 0.08)
    x_pad_right = max(plot_w * 0.075, 0.10)
    y_pad = max(plot_h * 0.055, 0.07)
    x_range = Range1d(x_min - x_pad_left, x_max + x_pad_right)
    y_range = Range1d(y_min - y_pad, y_max + y_pad)

    p = figure(
        width=900,
        height=480,
        sizing_mode='scale_width',
        x_range=x_range,
        y_range=y_range,
        tools='pan,wheel_zoom,reset,save',
        active_scroll='wheel_zoom',
    )
    p.min_border = 5
    apply_bokeh_figure_theme(p, plot_theme)
    p.xaxis.visible = False
    p.yaxis.visible = False
    p.grid.visible = False

    _add_aitoff_grid_and_labels(
        p,
        grid=grid,
        plot_x_min=x_min,
        plot_x_max=x_max,
        plot_y_min=y_min,
        plot_y_max=y_max,
        theme=plot_theme,
    )

    source = ColumnDataSource(data={
        'x': x,
        'y': y,
        'name': names,
        'ra': ra,
        'dec': dec,
        'distance_kpc': distances,
        'url': urls,
    })

    if colored_by_distance:
        color_mapper = _distance_color_mapper(distances)
        fill_color = linear_cmap(
            'distance_kpc',
            palette='Viridis256',
            low=color_mapper.low,
            high=color_mapper.high,
        )
        renderer = p.scatter(
            x='x',
            y='y',
            source=source,
            size=size,
            fill_color=fill_color,
            line_color=plot_theme.star_line,
            line_alpha=0.35,
            fill_alpha=0.9,
        )
        color_bar = _styled_color_bar(color_mapper, theme=plot_theme)
        p.add_layout(color_bar, 'right')
    else:
        renderer = p.scatter(
            x='x',
            y='y',
            source=source,
            size=size,
            fill_color=plot_theme.marker_fill,
            line_color=plot_theme.marker_line,
            line_alpha=0.35,
            fill_alpha=0.9,
        )

    hover = themed_hover_tool(
        renderers=[renderer],
        rows=[
            ('Name', '@name'),
            ('RA', '@ra{0.00000}°'),
            ('Dec', '@dec{0.00000}°'),
            ('Distance', '@distance_kpc{0.00} kpc'),
        ],
        theme=plot_theme,
    )
    p.add_tools(hover)
    p.add_tools(TapTool(renderers=[renderer], callback=OpenURL(url='@url')))

    return p
