import numpy as np
from bokeh import models as mpl
from bokeh import plotting as bpl
from bokeh.models import ColorBar, Range1d
from bokeh.palettes import Viridis9
from bokeh.transform import linear_cmap
from scipy import stats
from scipy.stats import pearsonr

from analysis.models import Parameter
from analysis.parameter_labels import parameter_axis_label, parse_cname
from analysis.services.parameter_consensus import (
    consensus_queryset,
    get_consensus_parameter,
    iter_project_consensus_cnames,
)
from stars.models import Star


def _finite_values(values):
    arr = np.asarray(values, dtype=float)
    return arr[np.isfinite(arr)]


def _normalize_color_column(values):
    arr = np.asarray(values, dtype=float)
    finite = np.isfinite(arr)
    if not np.any(finite):
        return None
    out = arr.copy()
    out[~finite] = np.nanmean(arr[finite])
    return out


def _normalize_size_column(values):
    arr = np.asarray(values, dtype=float)
    finite = np.isfinite(arr)
    if not np.any(finite):
        return None
    out = arr.copy()
    out[~finite] = np.nanmean(arr[finite])
    if np.ptp(out[finite]) > 1000:
        out = np.sqrt(np.maximum(out, 0))
    maxval = np.nanmax(out)
    if maxval == 0:
        return None
    return out / maxval * 0.025


def _set_axis_ranges(fig, xvals, yvals):
    finite_x = _finite_values(xvals)
    finite_y = _finite_values(yvals)

    if finite_x.size == 0:
        fig.x_range = Range1d(0, 1)
    else:
        x_ptp = np.ptp(finite_x)
        x_pad = x_ptp * 0.05 if x_ptp > 0 else 0.1
        fig.x_range = Range1d(np.min(finite_x) - x_pad, np.max(finite_x) + x_pad)

    if finite_y.size == 0:
        fig.y_range = Range1d(0, 1)
    else:
        y_ptp = np.ptp(finite_y)
        y_pad = y_ptp * 0.05 if y_ptp > 0 else 0.1
        fig.y_range = Range1d(np.min(finite_y) - y_pad, np.max(finite_y) + y_pad)


def _regression_confidence_band(x, y, confidence=0.95, n_points=100):
    """OLS fit with confidence band for the mean response."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = np.isfinite(x) & np.isfinite(y)
    x = x[mask]
    y = y[mask]
    n = x.size
    if n < 2:
        return None

    slope, intercept, _, _, _ = stats.linregress(x, y)
    if np.ptp(x) == 0:
        x_line = np.full(n_points, x[0])
    else:
        x_line = np.linspace(np.min(x), np.max(x), n_points)
    y_fit = intercept + slope * x_line

    dof = n - 2
    if dof < 1:
        return x_line, y_fit, None, None

    residuals = y - (intercept + slope * x)
    s_err = np.sqrt(np.sum(residuals ** 2) / dof)
    x_mean = np.mean(x)
    ss_x = np.sum((x - x_mean) ** 2)
    if ss_x == 0 or s_err == 0:
        return x_line, y_fit, None, None

    t_crit = stats.t.ppf((1 + confidence) / 2, dof)
    se_mean = s_err * np.sqrt(1 / n + (x_line - x_mean) ** 2 / ss_x)
    margin = t_crit * se_mean
    return x_line, y_fit, y_fit - margin, y_fit + margin


def _plot_regression_band(fig, regression):
    if regression is None:
        return
    x_line, _y_fit, y_lower, y_upper = regression
    if y_lower is None or y_upper is None:
        return
    fig.varea(
        x=x_line,
        y1=y_lower,
        y2=y_upper,
        fill_color='#64748b',
        fill_alpha=0.22,
        level='underlay',
    )


def _plot_regression_line(fig, regression):
    if regression is None:
        return
    x_line, y_fit, _y_lower, _y_upper = regression
    fig.line(
        x=x_line,
        y=y_fit,
        line_color='#f97316',
        line_width=2.5,
        line_alpha=0.95,
    )


def plot_errorbars(fig, x, y, xerr=None, yerr=None, **kwargs):
    """
    Plot errorbars on a bokeh plot
    """

    if xerr != None:
        err_xs, err_ys = [], []
        for x_, y_, err in zip(x, y, xerr):
            err_xs.append((x_ - err, x_ + err))
            err_ys.append((y_, y_))
        fig.multi_line(err_xs, err_ys, **kwargs)

    if yerr != None:
        err_xs, err_ys = [], []
        for x_, y_, err in zip(x, y, yerr):
            err_xs.append((x_, x_))
            err_ys.append((y_ - err, y_ + err))
        fig.multi_line(err_xs, err_ys, **kwargs)


def get_data(parameters, project=None):
    """
    Returns array with data for the requested parameters
    """

    pnames = set(parameters.values())
    pnames.discard('')

    params = consensus_queryset(project=project).filter(cname__in=pnames)
    stars = Star.objects.filter(
        pk__in=params.values_list('star', flat=True).distinct(),
    )
    if project is not None:
        stars = stars.filter(project=project)

    # -- get the parameter values
    parameter_table = {'system': [s.name for s in stars]}
    for pname in pnames:
        values, errors = [], []
        base, component = parse_cname(pname)
        for star in stars:
            p = get_consensus_parameter(star, base, component)
            if p is not None and p.cname == pname:
                values.append(p.value)
                errors.append(p.error)
            else:
                values.append(np.nan)
                errors.append(np.nan)
        parameter_table[pname] = values
        parameter_table['e_' + pname] = errors

    # dtypes = [('system', 'a50')] + [(str(p), 'f8') for p in pnames]
    # parameter_table = np.core.records.fromarrays(parameter_table, dtype=dtypes)

    return parameter_table, list(pnames)


def _parameter_units_by_cname(project=None):
    if project is not None:
        rows = iter_project_consensus_cnames(project)
    else:
        rows = consensus_queryset().values_list('cname', 'unit').distinct()
    return {cname: unit for cname, unit in rows}


def get_parameter_statistics(data, xpar, ypar, unit_lookup=None):
    try:
        x = np.asarray(data[xpar], dtype=float)
        y = np.asarray(data[ypar], dtype=float)
        mask = np.isfinite(x) & np.isfinite(y)
        if mask.sum() < 2:
            return "No statistics calculated"

        corr, pvalue = pearsonr(x[mask], y[mask])

        return "Pearson correlation ({} - {}) = {:0.2f},   P-value = {:0.3f}".format(
            parameter_axis_label(xpar, (unit_lookup or {}).get(xpar)),
            parameter_axis_label(ypar, (unit_lookup or {}).get(ypar)),
            corr, pvalue,
        )
    except Exception:
        return "No statistics calculated"


def plot_parameters(parameters, project=None, show_regression=False, **kwargs):
    """
    Makes a simple plot of the given parameters
    """
    xpar = parameters.get('xaxis', 'parallax')
    ypar = parameters.get('yaxis', 'pmdec')
    rstr = parameters.get('size') or None
    cstr = parameters.get('color') or None
    if rstr == '':
        rstr = None
    if cstr == '':
        cstr = None

    data, param_names = get_data(parameters, project=project)
    unit_lookup = _parameter_units_by_cname(project=project)
    for par in (xpar, ypar, rstr, cstr):
        if par:
            data.setdefault(par, [])
            data.setdefault(f'e_{par}', [])
    statistics = get_parameter_statistics(data, xpar, ypar, unit_lookup=unit_lookup)

    norm_cstr = None
    if cstr is not None:
        norm_cstr = _normalize_color_column(data[cstr])
        if norm_cstr is None:
            cstr = None
        else:
            data['norm_' + cstr] = norm_cstr

    if rstr is not None:
        norm_rstr = _normalize_size_column(data[rstr])
        if norm_rstr is None:
            rstr = None
        else:
            data['norm_' + rstr] = norm_rstr

    # -- datasource for bokeh
    datasource = bpl.ColumnDataSource(data=data)

    tooltips = [('System', '@system')] + \
               [(parameter_axis_label(p, unit_lookup.get(p)),
                 '@{} +- @e_{}'.format(p, p)) for p in param_names]

    TOOLS = [mpl.PanTool(), mpl.WheelZoomTool(),
             mpl.BoxZoomTool(), mpl.ResetTool()]

    fig = bpl.figure(
        width=800,
        height=600,
        toolbar_location='right',
        tools=TOOLS,
        sizing_mode='scale_width',
    )

    regression = None
    if show_regression:
        regression = _regression_confidence_band(data[xpar], data[ypar])
        _plot_regression_band(fig, regression)

    default_radius = 0.03

    if rstr is not None and cstr is not None:
        colors = linear_cmap(
            'norm_' + cstr,
            palette=Viridis9,
            low=np.amin(norm_cstr),
            high=np.amax(norm_cstr),
        )
        main_plot = fig.circle(
            source=datasource,
            name='main',
            x=xpar,
            y=ypar,
            radius='norm_' + rstr,
            alpha=0.7,
            fill_color=colors,
            line_color=colors,
        )
        color_bar = ColorBar(
            color_mapper=colors['transform'],
            width=8,
            location=(0, 0),
            title=parameter_axis_label(cstr, unit_lookup.get(cstr)),
        )
        fig.add_layout(color_bar, 'right')
    elif rstr is not None:
        main_plot = fig.circle(
            source=datasource,
            name='main',
            x=xpar,
            y=ypar,
            radius='norm_' + rstr,
            alpha=0.7,
        )
    elif cstr is not None:
        colors = linear_cmap(
            'norm_' + cstr,
            palette=Viridis9,
            low=np.amin(norm_cstr),
            high=np.amax(norm_cstr),
        )
        main_plot = fig.circle(
            source=datasource,
            name='main',
            x=xpar,
            y=ypar,
            radius=default_radius,
            alpha=0.7,
            fill_color=colors,
            line_color=colors,
        )
        color_bar = ColorBar(
            color_mapper=colors['transform'],
            width=8,
            location=(0, 0),
            title=parameter_axis_label(cstr, unit_lookup.get(cstr)),
        )
        fig.add_layout(color_bar, 'right')
    else:
        main_plot = fig.circle(
            source=datasource,
            name='main',
            x=xpar,
            y=ypar,
            radius=default_radius,
            alpha=0.7,
        )

    _set_axis_ranges(fig, data[xpar], data[ypar])

    if xpar != '':
        plot_errorbars(
            fig, data[xpar], data[ypar],
            xerr=data['e_' + xpar], yerr=data['e_' + ypar],
        )

    if show_regression:
        _plot_regression_line(fig, regression)

    hover = mpl.HoverTool(tooltips=tooltips, renderers=[main_plot])
    fig.add_tools(hover)

    fig.toolbar.logo = None
    fig.yaxis.axis_label = parameter_axis_label(ypar, unit_lookup.get(ypar))
    fig.xaxis.axis_label = parameter_axis_label(xpar, unit_lookup.get(xpar))
    fig.yaxis.axis_label_text_font_size = '10pt'
    fig.xaxis.axis_label_text_font_size = '10pt'
    fig.min_border = 5

    return fig, statistics
