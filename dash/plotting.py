from django.conf import settings

import os

import numpy as np
from bokeh import models as mpl
from bokeh import plotting as bpl
from bokeh.models import Range1d
from bokeh.palettes import Viridis9
from bokeh.transform import linear_cmap
from django.contrib import messages

from astropy.table import QTable

from analysis.parameter_labels import hrd_axis_label, normalize_hrd_axis_key
from dash.bokeh_theme import apply_bokeh_figure_theme, resolve_bokeh_theme, styled_color_bar, themed_hover_tool
from stars.models import Project, Star

_MISSING = -1000.0


def _consensus_axis_value(star, name, components=(1, 2, 0)):
    """First available consensus value for an HRD axis parameter."""
    from analysis.services.parameter_consensus import get_consensus_parameter

    for component in components:
        param = get_consensus_parameter(star, name, component)
        if param is not None:
            return param.value, (param.error_l + param.error_u) / 2.0
    return None, None


def _consensus_axis_or_sentinel(star, name, components=(1, 2, 0)):
    value, error = _consensus_axis_value(star, name, components)
    if value is None:
        return _MISSING, _MISSING
    if error is None:
        error = 0.0
    return value, error


def errors_from_coords(x, y, x_err, y_err):
    x_err[x_err == -1000] = 0
    y_err[y_err == -1000] = 0

    x_upper = x + x_err
    x_lower = x - x_err

    y_upper = y + y_err
    y_lower = y - y_err

    return list(zip(x_upper, x_lower)), list(zip(y_upper, y_lower)), list(zip(x, x)), list(zip(y, y))


def _plot_error_bars(fig, x_errcoords, y_errcoords, empty_x, empty_y, *, theme):
    style = {'line_color': theme.error_line, 'line_alpha': 0.55}
    fig.multi_line(x_errcoords, empty_y, **style)
    fig.multi_line(empty_x, y_errcoords, **style)


def plot_hrd(request, project_id, xstr="bp_rp", ystr="absolute_g_mag", rstr=None,
             cstr=None, nstars=50, *, theme=None):
    plot_theme = resolve_bokeh_theme(theme)
    if rstr == "":
        rstr = None
    if cstr == "":
        cstr = None
    xstr = normalize_hrd_axis_key(xstr)
    ystr = normalize_hrd_axis_key(ystr)
    if rstr:
        rstr = normalize_hrd_axis_key(rstr)
    if cstr:
        cstr = normalize_hrd_axis_key(cstr)
    proj = Project.objects.get(pk=project_id)
    if nstars == "all":
        star_list = Star.objects.filter(project=proj).prefetch_related('parameter_set')
    else:
        nstars = int(nstars)
        star_list = Star.objects.filter(project=proj).prefetch_related('parameter_set')[:nstars]

    idents = list(star_list.values_list('name', flat=True))
    teffs = []
    teffs_errs = []
    loggs = []
    loggs_errs = []
    bp_rps = []
    bp_rps_errs = []
    mags = []
    mags_errs = []
    g_mag_abss = []
    g_mag_abs_errs = []

    for star in star_list:
        teff, tefferr = _consensus_axis_or_sentinel(star, 'teff')
        logg, loggerr = _consensus_axis_or_sentinel(star, 'logg')
        mag, magerr = _consensus_axis_or_sentinel(star, 'mag', components=(0,))
        bp_rp, bp_rp_err = _consensus_axis_or_sentinel(star, 'bp_rp', components=(0,))
        g_mag_abs, g_mag_abs_err = _consensus_axis_or_sentinel(
            star, 'absolute_g_mag', components=(0,),
        )

        mags.append(mag)
        mags_errs.append(magerr)
        teffs.append(teff)
        teffs_errs.append(tefferr)
        loggs.append(logg)
        loggs_errs.append(loggerr)
        bp_rps.append(bp_rp)
        bp_rps_errs.append(bp_rp_err)
        g_mag_abss.append(g_mag_abs)
        g_mag_abs_errs.append(g_mag_abs_err)
    star_props = dict(idents=idents,
                      teff=np.array(teffs),
                      teff_errs=np.array(teffs_errs),
                      logg=np.array(loggs),
                      logg_errs=np.array(loggs_errs),
                      mag=np.array(mags),
                      mag_errs=np.array(mags_errs),
                      bp_rp=np.array(bp_rps),
                      bp_rp_errs=np.array(bp_rps_errs),
                      absolute_g_mag=np.array(g_mag_abss),
                      absolute_g_mag_errs=np.array(g_mag_abs_errs),
                      )

    if cstr is not None:
        normcstr = star_props[cstr]
        if sum(normcstr != _MISSING) == 0:
            cstr = None
        else:
            normcstr[normcstr == _MISSING] = np.mean(normcstr[normcstr != _MISSING])
            star_props["norm_" + cstr] = normcstr
    if rstr is not None:
        normrstr = star_props[rstr]
        if sum(normrstr != _MISSING) == 0:
            rstr = None
        else:
            normrstr[normrstr == _MISSING] = np.mean(normrstr[normrstr != _MISSING])
            if np.ptp(normrstr) > 1000:
                normrstr = np.sqrt(normrstr)
            normrstr = normrstr / np.amax(normrstr) * .025
            star_props["norm_" + rstr] = normrstr

    if ystr == "absolute_g_mag":
        if sum(star_props['absolute_g_mag'] != _MISSING) == 0:
            ystr = "mag"
            messages.warning(request,
                             "Absolute g-band magnitudes are not available, instead apparent magnitudes are plotted.")

    starsource = bpl.ColumnDataSource(data=star_props)

    tools = [mpl.PanTool(), mpl.WheelZoomTool(),
             mpl.BoxZoomTool(), mpl.ResetTool()]
    fig = bpl.figure(width=1150, height=475, tools=tools, sizing_mode='scale_width')

    # fig.circle(wave, meas)
    # fig.circle('bp_rp', 'mag', size=8, color='white', alpha=0.1, name='hover', source=starsource)

    #   Add Gaia data for CMD plots
    if xstr == "bp_rp" and ystr == "absolute_g_mag":
        #   Read data from file
        gaia_data = QTable.read(
            os.path.join(settings.BASE_DIR, 'media/gaia/gaia_data.fits')
        )
        gaia_mag = gaia_data['g_mag_abs'].value.astype(np.float16)
        gaia_color = gaia_data['bp_rp'].value.astype(np.float16)

        fig.scatter(
            x=gaia_color,
            y=gaia_mag,
            size=10,
            marker='dot',
            color=plot_theme.gaia_reference,
            alpha=plot_theme.gaia_reference_alpha,
        )

    if rstr is not None and cstr is not None:
        colors = linear_cmap("norm_" + cstr, palette=Viridis9, low=np.amin(normcstr),
                             high=np.amax(normcstr))

        x_errcoords, y_errcoords, empty_x, empty_y = errors_from_coords(star_props[xstr], star_props[ystr],
                                                                        star_props[xstr + "_errs"],
                                                                        star_props[ystr + "_errs"])

        _plot_error_bars(
            fig, x_errcoords, y_errcoords, empty_x, empty_y, theme=plot_theme,
        )

        main_plot = fig.circle(source=starsource,
                                name="main",
                                x=xstr,
                                y=ystr,
                                radius="norm_" + rstr,
                                alpha=.7,
                                fill_color=colors,
                                line_color=colors)

        color_bar = styled_color_bar(
            colors['transform'],
            theme=plot_theme,
            title=hrd_axis_label(cstr),
        )

        fig.add_layout(color_bar, 'right')

    elif rstr is not None:
        x_errcoords, y_errcoords, empty_x, empty_y = errors_from_coords(star_props[xstr], star_props[ystr],
                                                                        star_props[xstr + "_errs"],
                                                                        star_props[ystr + "_errs"])

        _plot_error_bars(
            fig, x_errcoords, y_errcoords, empty_x, empty_y, theme=plot_theme,
        )

        main_plot = fig.circle(source=starsource,
                                name="main",
                                x=xstr,
                                y=ystr,
                                radius="norm_" + rstr,
                                alpha=.7,
                                fill_color=plot_theme.marker_fill,
                                line_color=plot_theme.marker_line)

    elif cstr is not None:
        colors = linear_cmap("norm_" + cstr, palette=Viridis9, low=np.amin(star_props["norm_" + cstr]),
                             high=np.amax(star_props["norm_" + cstr]))

        x_errcoords, y_errcoords, empty_x, empty_y = errors_from_coords(star_props[xstr], star_props[ystr],
                                                                        star_props[xstr + "_errs"],
                                                                        star_props[ystr + "_errs"])

        _plot_error_bars(
            fig, x_errcoords, y_errcoords, empty_x, empty_y, theme=plot_theme,
        )

        main_plot = fig.circle(source=starsource,
                                name="main",
                                x=xstr,
                                y=ystr,
                                radius=.03,
                                alpha=.7,
                                fill_color=colors,
                                line_color=colors)

        color_bar = styled_color_bar(
            colors['transform'],
            theme=plot_theme,
            title=hrd_axis_label(cstr),
        )

        fig.add_layout(color_bar, 'right')

    else:
        x_errcoords, y_errcoords, empty_x, empty_y = errors_from_coords(star_props[xstr], star_props[ystr],
                                                                        star_props[xstr + "_errs"],
                                                                        star_props[ystr + "_errs"])

        _plot_error_bars(
            fig, x_errcoords, y_errcoords, empty_x, empty_y, theme=plot_theme,
        )

        main_plot = fig.circle(source=starsource,
                                name="main",
                                x=xstr,
                                y=ystr,
                                radius=.03,
                                alpha=.7,
                                fill_color=plot_theme.marker_fill,
                                line_color=plot_theme.marker_line)

    # fig.circle(x=xstr, y=ystr, source=starsource, size=5)

    hover = themed_hover_tool(
        renderers=[main_plot],
        rows=[
            ('System', '@idents'),
            ('T_eff', '@teff'),
            ('log(g)', '@logg'),
            ('magnitude', '@mag'),
        ],
        theme=plot_theme,
    )

    fig.add_tools(hover)

    x = star_props[xstr][np.where(star_props[xstr] != _MISSING)]
    y = star_props[ystr][np.where(star_props[ystr] != _MISSING)]

    try:
        fig.x_range = Range1d(
            np.amin(x) - np.ptp(x) * 0.05,
            np.amax(x) + np.ptp(x) * 0.05
        )
        fig.y_range = Range1d(
            np.amin(y) - np.ptp(y) * 0.05,
            np.amax(y) + np.ptp(y) * 0.05
        )

        if ystr == "mag":
            fig.y_range = Range1d(
                np.amax(y) + np.ptp(y) * 0.05,
                np.amin(y) - np.ptp(y) * 0.05
            )

        if xstr == "mag":
            fig.x_range = Range1d(
                np.amax(x) + np.ptp(x) * 0.05,
                np.amin(x) - np.ptp(x) * 0.05
            )

        #   Plot limits for CMD with Gaia data
        if xstr == "bp_rp" and ystr == "absolute_g_mag":
            fig.y_range = Range1d(
                max(np.nanmax(y), np.nanmax(gaia_mag)) + (np.nanmax(y) - np.nanmin(y)) * 0.05,
                min(np.nanmin(y), np.nanmin(gaia_mag)) - (np.nanmax(y) - np.nanmin(y)) * 0.05
            )

            fig.x_range = Range1d(
                min(np.nanmin(x), np.nanmin(gaia_color)) - np.ptp(x) * 0.05,
                max(np.nanmax(x), np.nanmax(gaia_color)) + np.ptp(x) * 0.05
            )

    except ValueError:
        # If no datapoints exist for x or y for some reason
        fig.x_range = Range1d(0, 1)
        fig.y_range = Range1d(0, 1)

        messages.error(request,
                       "Plotting failed. Check if the stars in your project have the parameters you want to plot.")

    fig.toolbar.logo = None

    fig.yaxis.axis_label = hrd_axis_label(ystr)
    fig.xaxis.axis_label = hrd_axis_label(xstr)
    fig.yaxis.axis_label_text_font_size = '10pt'
    fig.xaxis.axis_label_text_font_size = '10pt'
    fig.min_border = 5
    apply_bokeh_figure_theme(fig, plot_theme)

    return fig
