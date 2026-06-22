"""Bokeh plot colors aligned with SPA theme tokens (frontend/src/style.css)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ThemeMode = Literal['dark', 'light']


@dataclass(frozen=True)
class BokehPlotTheme:
    """Plot canvas may contrast slightly with ``plot_border`` / ``colorbar_background`` (panel surface)."""

    plot_background: str
    plot_border: str
    outline: str
    grid_line: str
    grid_line_alpha: float
    axis_line: str
    tick_line: str
    tick_text: str
    axis_title: str
    colorbar_background: str
    colorbar_title: str
    colorbar_label: str
    star_line: str
    error_line: str
    marker_fill: str
    marker_line: str
    gaia_reference: str
    gaia_reference_alpha: float
    tooltip_background: str
    tooltip_text: str
    tooltip_border: str


THEMES: dict[ThemeMode, BokehPlotTheme] = {
    'dark': BokehPlotTheme(
        plot_background='#151f2e',
        plot_border='#1e293b',
        outline='#475569',
        grid_line='#475569',
        grid_line_alpha=0.32,
        axis_line='#475569',
        tick_line='#475569',
        tick_text='#cbd5e1',
        axis_title='#e2e8f0',
        colorbar_background='#1e293b',
        colorbar_title='#e2e8f0',
        colorbar_label='#94a3b8',
        star_line='#ffffff',
        error_line='#64748b',
        marker_fill='#38bdf8',
        marker_line='#cbd5e1',
        gaia_reference='#64748b',
        gaia_reference_alpha=0.28,
        tooltip_background='#1e293b',
        tooltip_text='#e2e8f0',
        tooltip_border='#475569',
    ),
    'light': BokehPlotTheme(
        plot_background='#f3f6f9',
        plot_border='#ffffff',
        outline='#c5d5dd',
        grid_line='#94a3b8',
        grid_line_alpha=0.45,
        axis_line='#c5d5dd',
        tick_line='#94a3b8',
        tick_text='#666666',
        axis_title='#333333',
        colorbar_background='#ffffff',
        colorbar_title='#333333',
        colorbar_label='#666666',
        star_line='#334155',
        error_line='#94a3b8',
        marker_fill='#4682b4',
        marker_line='#334155',
        gaia_reference='#9db3d1',
        gaia_reference_alpha=0.55,
        tooltip_background='#ffffff',
        tooltip_text='#333333',
        tooltip_border='#c5d5dd',
    ),
}


def resolve_bokeh_theme(value: str | None) -> BokehPlotTheme:
    if value == 'light':
        return THEMES['light']
    return THEMES['dark']


def apply_bokeh_figure_theme(fig, theme: BokehPlotTheme) -> None:
    """Canvas contrasts with panel; border area matches template surface."""
    fig.background_fill_color = theme.plot_background
    fig.border_fill_color = theme.plot_border
    fig.outline_line_color = theme.outline

    for axis in (fig.xaxis, fig.yaxis):
        axis.axis_label_text_color = theme.axis_title
        axis.major_label_text_color = theme.tick_text
        axis.axis_line_color = theme.axis_line
        axis.major_tick_line_color = theme.tick_line
        axis.minor_tick_line_color = theme.tick_line

    fig.grid.grid_line_color = theme.grid_line
    fig.grid.minor_grid_line_color = theme.grid_line
    fig.grid.grid_line_alpha = theme.grid_line_alpha
    fig.grid.minor_grid_line_alpha = theme.grid_line_alpha * 0.65

    legend = getattr(fig, 'legend', None)
    if legend is not None:
        try:
            has_legend = bool(legend.items)
        except AttributeError:
            has_legend = len(legend) > 0
        if has_legend:
            legend.background_fill_color = theme.plot_border
            legend.border_line_color = theme.outline
            legend.label_text_color = theme.tick_text
            legend.title_text_color = theme.axis_title

    if fig.title is not None:
        fig.title.text_color = theme.axis_title


def styled_color_bar(color_mapper, *, theme: BokehPlotTheme, title: str, width: int = 8) -> 'ColorBar':
    from bokeh.models import ColorBar

    return ColorBar(
        color_mapper=color_mapper,
        title=title,
        width=width,
        location=(0, 0),
        background_fill_color=theme.colorbar_background,
        background_fill_alpha=1.0,
        border_line_color=None,
        title_text_color=theme.colorbar_title,
        major_label_text_color=theme.colorbar_label,
    )


def _themed_tooltip_html(body: str, theme: BokehPlotTheme) -> str:
    return f"""<style>:host {{
  background-color: {theme.tooltip_background};
  color: {theme.tooltip_text};
  border: 1px solid {theme.tooltip_border};
  padding: 6px 8px;
  font-size: 12px;
  line-height: 1.35;
}}</style>{body}"""


def themed_hover_tool(*, renderers, rows: list[tuple[str, str]], theme: BokehPlotTheme) -> 'HoverTool':
    """Hover tooltips styled for dark/light panel (Bokeh 3 shadow DOM :host)."""
    from bokeh.models import HoverTool

    body = ''.join(
        f'<div><span style="opacity:0.8">{label}:</span> {value}</div>'
        for label, value in rows
    )
    return HoverTool(renderers=renderers, tooltips=_themed_tooltip_html(body, theme))


def themed_field_hover_tool(
    *,
    renderers,
    tooltips: list[tuple[str, str]],
    theme: BokehPlotTheme,
) -> 'HoverTool':
    """Hover tool with Bokeh field references (@column) and themed tooltip chrome."""
    from bokeh.models import HoverTool

    body = ''.join(
        f'<div><span style="opacity:0.8">{label}:</span> {field}</div>'
        for label, field in tooltips
    )
    return HoverTool(renderers=renderers, tooltips=_themed_tooltip_html(body, theme))


def themed_status_label(
    *,
    x,
    y,
    text: str,
    theme: BokehPlotTheme,
    text_color: str = '#ef4444',
    **kwargs,
) -> 'Label':
    """On-plot status/error label matching panel surface."""
    from bokeh.models import Label

    return Label(
        x=x,
        y=y,
        text=text,
        text_color=text_color,
        text_align=kwargs.pop('text_align', 'center'),
        text_baseline=kwargs.pop('text_baseline', 'middle'),
        background_fill_color=theme.plot_border,
        background_fill_alpha=1.0,
        border_line_color=theme.outline,
        border_line_alpha=1.0,
        **kwargs,
    )
