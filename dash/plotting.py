import time

from django.db import reset_queries, connection
import numpy as np
from bokeh import models as mpl
from bokeh import plotting as bpl
from bokeh.models import ColorBar, Range1d
from bokeh.palettes import Viridis9
from bokeh.transform import linear_cmap
from django.contrib import messages

from django.db.models import Prefetch

from analysis.models import Parameter
from observations.models import Photometry
from stars.models import Project, Star
from .labels import labeldict


def errors_from_coords(x, y, x_err, y_err):
    x_err[x_err == -1000] = 0
    y_err[y_err == -1000] = 0

    x_upper = x + x_err
    x_lower = x - x_err

    y_upper = y + y_err
    y_lower = y - y_err

    return list(zip(x_upper, x_lower)), list(zip(y_upper, y_lower)), list(zip(x, x)), list(zip(y, y))


def plot_hrd(request, project_id, xstr="bp_rp", ystr="mag", rstr=None, cstr=None, nstars=50):
    # reset_queries()
    if rstr == "":
        rstr = None
    if cstr == "":
        cstr = None
    proj = Project.objects.get(pk=project_id)
    if nstars == "all":
        star_list = Star.objects.filter(project=proj).prefetch_related('parameter_set', 'photometry_set')
    else:
        nstars = int(nstars)
        star_list = Star.objects.filter(project=proj).prefetch_related('parameter_set', 'photometry_set')[:nstars]

    idents = list(star_list.values_list('name', flat=True))
    teffs = []
    teffs_errs = []
    loggs = []
    loggs_errs = []
    bp_rps = []
    bp_rps_errs = []
    mags = []
    mags_errs = []

    for star in star_list:
        pset = list(star.parameter_set.values_list("name", "data_source", "value", "error_l", "error_u"))
        photset = list(star.photometry_set.values_list("band", "measurement", "error"))

        mag = None
        magerr = None
        bp_rp = 0
        bp_rp_err = 0
        bp_in = False
        rp_in = False

        for band, val, err in photset:
            if "GAIA" in band and ".G" in band:
                mag = val
                magerr = err
            if ".BP" in band and not bp_in:
                bp_rp += val
                bp_rp_err += err
                bp_in = True
            if ".RP" in band and not rp_in:
                bp_rp -= val
                bp_rp_err += err
                rp_in = True
        if mag is None or magerr is None:
            mag = magerr = -1000.

        bp_rp_err /= 2

        teff = None
        tefferr = None
        logg = None
        loggerr = None

        for name, data_source, val, err_l, err_u in pset:
            if data_source != "AVG":
                continue
            if name == "teff":
                teff = val
                tefferr = (err_l + err_u) / 2
            if name == "log_g":
                logg = val
                loggerr = (err_l + err_u) / 2
            if name == "bp_rp" and bp_rp == 0:
                bp_rp = val
                bp_rp_err = (err_l + err_u) / 2

        if teff is None or tefferr is None:
            teff = tefferr = -1000.
        if logg is None or loggerr is None:
            logg = loggerr = -1000.
        if bp_rp == 0 or bp_rp_err == 0:
            bp_rp = bp_rp_err = -1000.

        mags.append(mag)
        mags_errs.append(magerr)
        teffs.append(teff)
        teffs_errs.append(tefferr)
        loggs.append(logg)
        loggs_errs.append(loggerr)
        bp_rps.append(bp_rp)
        bp_rps_errs.append(bp_rp_err)

    # print(len(connection.queries))
    star_props = dict(idents=idents,
                      teff=np.array(teffs),
                      teff_errs=np.array(teffs_errs),
                      logg=np.array(loggs),
                      logg_errs=np.array(loggs_errs),
                      mag=np.array(mags),
                      mag_errs=np.array(mags_errs),
                      bp_rp=np.array(bp_rps),
                      bp_rp_errs=np.array(bp_rps_errs))

    if cstr is not None:
        normcstr = star_props[cstr]
        if sum(normcstr != -1000.) == 0:
            cstr = None
        else:
            normcstr[normcstr == -1000.] = np.mean(normcstr[normcstr != -1000.])
            star_props["norm_" + cstr] = normcstr
    if rstr is not None:
        normrstr = star_props[rstr]
        if sum(normrstr != -1000.) == 0:
            rstr = None
        else:
            normrstr[normrstr == -1000.] = np.mean(normrstr[normrstr != -1000.])
            if np.ptp(normrstr) > 1000:
                normrstr = np.sqrt(normrstr)
            normrstr = normrstr / np.amax(normrstr) * .025
            star_props["norm_" + rstr] = normrstr

    starsource = bpl.ColumnDataSource(data=star_props)

    tools = [mpl.PanTool(), mpl.WheelZoomTool(),
             mpl.BoxZoomTool(), mpl.ResetTool()]
    fig = bpl.figure(width=840, height=475, tools=tools)

    # fig.circle(wave, meas)
    # fig.circle('bp_rp', 'mag', size=8, color='white', alpha=0.1, name='hover', source=starsource)

    # #   Add Gaia data for CMD plots
    # if xstr=="bp_rp" and ystr=="mag":
    #     #   Read data from file
    #     gaia_data = QTable.read(
    #         os.path.join(settings.BASE_DIR, 'media/gaia/gaia_data.fits')
    #         )
    #     gaia_mag = gaia_data['g_mag_abs'].value
    #     gaia_color = gaia_data['bp_rp'].value
    #
    #     fig.dot(
    #         x=gaia_color,
    #         y=gaia_mag,
    #         size=7,
    #         # color="#cccccc",
    #         color="#9db3d1",
    #         )

    if rstr is not None and cstr is not None:
        colors = linear_cmap("norm_" + cstr, palette=Viridis9, low=np.amin(normcstr),
                             high=np.amax(normcstr))

        x_errcoords, y_errcoords, empty_x, empty_y = errors_from_coords(star_props[xstr], star_props[ystr],
                                                                        star_props[xstr + "_errs"],
                                                                        star_props[ystr + "_errs"])

        fig.multi_line(x_errcoords, empty_y)
        fig.multi_line(empty_x, y_errcoords)

        main_plot = fig.scatter(source=starsource,
                                name="main",
                                x=xstr,
                                y=ystr,
                                radius="norm_" + rstr,
                                marker="circle",
                                alpha=.7,
                                fill_color=colors,
                                line_color=colors)

        color_bar = ColorBar(color_mapper=colors['transform'], width=8, location=(0, 0), title=labeldict[cstr])

        fig.add_layout(color_bar, 'right')

    elif rstr is not None:
        x_errcoords, y_errcoords, empty_x, empty_y = errors_from_coords(star_props[xstr], star_props[ystr],
                                                                        star_props[xstr + "_errs"],
                                                                        star_props[ystr + "_errs"])

        fig.multi_line(x_errcoords, empty_y)
        fig.multi_line(empty_x, y_errcoords)

        main_plot = fig.scatter(source=starsource,
                                name="main",
                                x=xstr,
                                y=ystr,
                                radius="norm_" + rstr,
                                marker="circle",
                                alpha=.7)

    elif cstr is not None:
        colors = linear_cmap("norm_" + cstr, palette=Viridis9, low=np.amin(star_props["norm_" + cstr]),
                             high=np.amax(star_props["norm_" + cstr]))

        x_errcoords, y_errcoords, empty_x, empty_y = errors_from_coords(star_props[xstr], star_props[ystr],
                                                                        star_props[xstr + "_errs"],
                                                                        star_props[ystr + "_errs"])

        fig.multi_line(x_errcoords, empty_y)
        fig.multi_line(empty_x, y_errcoords)

        main_plot = fig.scatter(source=starsource,
                                name="main",
                                x=xstr,
                                y=ystr,
                                marker="circle",
                                radius=.03,
                                alpha=.7,
                                fill_color=colors,
                                line_color=colors)

        color_bar = ColorBar(color_mapper=colors['transform'], width=8, location=(0, 0), title=labeldict[cstr])

        fig.add_layout(color_bar, 'right')

    else:
        x_errcoords, y_errcoords, empty_x, empty_y = errors_from_coords(star_props[xstr], star_props[ystr],
                                                                        star_props[xstr + "_errs"],
                                                                        star_props[ystr + "_errs"])

        fig.multi_line(x_errcoords, empty_y)
        fig.multi_line(empty_x, y_errcoords)

        main_plot = fig.scatter(source=starsource,
                                name="main",
                                x=xstr,
                                y=ystr,
                                radius=.03,
                                marker="circle",
                                alpha=.7, )

    # fig.circle(x=xstr, y=ystr, source=starsource, size=5)

    hover = mpl.HoverTool(tooltips=[("System", "@idents"),
                                    ("T_eff", "@teff"),
                                    ("log(g)", "@logg"),
                                    ("magnitude", "@mag")],
                          renderers=[main_plot])

    fig.add_tools(hover)

    x = star_props[xstr][np.where(star_props[xstr] != -1000)]
    y = star_props[ystr][np.where(star_props[ystr] != -1000)]

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
        # if xstr == "bp_rp" and ystr == "mag":
        #     fig.y_range = Range1d(
        #         max(np.amax(y), np.amax(gaia_mag)) + np.ptp(y) * 0.05,
        #         min(np.amin(y), np.amin(gaia_mag)) - np.ptp(y) * 0.05
        #         )
        #
        #     fig.x_range = Range1d(
        #     min(np.amin(x), np.amin(gaia_color)) - np.ptp(x) * 0.05,
        #     max(np.amax(x), np.amax(gaia_color)) + np.ptp(x) * 0.05
        #     )

    except ValueError:
        # If no datapoints exist for x or y for some reason
        fig.x_range = Range1d(0, 1)
        fig.y_range = Range1d(0, 1)

        messages.error(request,
                       "Plotting failed. Check if the stars in your project have the parameters you want to plot.")

    fig.toolbar.logo = None

    fig.yaxis.axis_label = labeldict[ystr]
    fig.xaxis.axis_label = labeldict[xstr]
    fig.yaxis.axis_label_text_font_size = '10pt'
    fig.xaxis.axis_label_text_font_size = '10pt'
    fig.min_border = 5

    return fig
