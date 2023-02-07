import numpy as np
from bokeh import models as mpl
from bokeh import plotting as bpl
from bokeh.models import ColorBar, Range1d
from bokeh.palettes import Viridis9
from bokeh.transform import linear_cmap

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


def plot_hrd(project_id, xstr="bp_rp", ystr="mag", rstr=None, cstr=None, nstars=100):
    if rstr == "":
        rstr = None
    if cstr == "":
        cstr = None

    proj = Project.objects.get(pk=project_id)
    star_list = Star.objects.filter(project=proj)
    if nstars != "all":
        nstars = int(nstars)
        star_list = star_list[:nstars]

    # I would rather not use a for loop here, but I don't have a better idea

    teffs = []
    teffs_errs = []
    loggs = []
    loggs_errs = []
    bp_rps = []
    bp_rps_errs = []
    mags = []
    mags_errs = []
    idents = []

    for star in star_list:
        name = star.name
        idents.append(name)
        pset = star.parameter_set.all()
        photset = star.photometry_set.all()
        try:
            magset = photset.filter(band__icontains='.G')
            mag = sum([m.measurement for m in magset]) / len(magset)
            magerr = np.sqrt(sum([m.error ** 2 for m in magset]) / len(magset))
        except ZeroDivisionError:
            mag = magerr = -1000.
        try:
            t = pset.filter(name__icontains='teff', data_source__name="AVG")[0]
            teff = t.value
            tefferr = t.error
        except:
            teff = tefferr = -1000.
        try:
            l = pset.filter(name__icontains='log_g', data_source__name="AVG")[0]
            logg, loggerr = [l.value, l.error]
        except:
            logg = loggerr = -1000.
        try:
            b = pset.filter(name__icontains='bp_rp', data_source__name="AVG")[0]
            assert len(b) > 0
            bp_rp = b.value
            bp_rp_err = b.error
        except:
            try:
                bp = photset.filter(band__icontains=".BP")
                rp = photset.filter(band__icontains=".RP")

                bp_rp = bp[0].measurement - rp[0].measurement
                bp_rp_err = np.sqrt(bp[0].error ** 2 + rp[0].error ** 2)
            except IndexError:
                bp_rp = bp_rp_err = -1000.

        mags.append(mag)
        mags_errs.append(magerr)
        teffs.append(teff)
        teffs_errs.append(tefferr)
        loggs.append(logg)
        loggs_errs.append(loggerr)
        bp_rps.append(bp_rp)
        bp_rps_errs.append(bp_rp_err)

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
    hover = mpl.HoverTool(tooltips=[("System", "@idents"),
                                    ("T_eff", "@teff"),
                                    ("log(g)", "@logg"),
                                    ("magnitude", "@mag")],
                          names=["main"])

    tools = [mpl.PanTool(), mpl.WheelZoomTool(),
             mpl.BoxZoomTool(), mpl.ResetTool(), hover]
    fig = bpl.figure(plot_width=700, plot_height=400, tools=tools)

    # fig.circle(wave, meas)
    # fig.circle('bp_rp', 'mag', size=8, color='white', alpha=0.1, name='hover', source=starsource)

    if rstr is not None and cstr is not None:
        colors = linear_cmap("norm_" + cstr, palette=Viridis9, low=np.amin(normcstr),
                             high=np.amax(normcstr))

        x_errcoords, y_errcoords, empty_x, empty_y = errors_from_coords(star_props[xstr], star_props[ystr], star_props[xstr + "_errs"], star_props[ystr + "_errs"])

        fig.multi_line(x_errcoords, empty_y)
        fig.multi_line(empty_x, y_errcoords)

        fig.scatter(source=starsource,
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
        x_errcoords, y_errcoords, empty_x, empty_y = errors_from_coords(star_props[xstr], star_props[ystr], star_props[xstr + "_errs"], star_props[ystr + "_errs"])

        fig.multi_line(x_errcoords, empty_y)
        fig.multi_line(empty_x, y_errcoords)

        fig.scatter(source=starsource,
                    name="main",
                    x=xstr,
                    y=ystr,
                    radius="norm_" + rstr,
                    marker="circle",
                    alpha=.7)


    elif cstr is not None:
        colors = linear_cmap("norm_" + cstr, palette=Viridis9, low=np.amin(star_props["norm_" + cstr]),
                             high=np.amax(star_props["norm_" + cstr]))

        x_errcoords, y_errcoords, empty_x, empty_y = errors_from_coords(star_props[xstr], star_props[ystr], star_props[xstr + "_errs"], star_props[ystr + "_errs"])

        fig.multi_line(x_errcoords, empty_y)
        fig.multi_line(empty_x, y_errcoords)

        fig.scatter(source=starsource,
                    name="main",
                    x=xstr,
                    y=ystr,
                    marker="circle",
                    radius=.015,
                    alpha=.7,
                    fill_color=colors,
                    line_color=colors)

        color_bar = ColorBar(color_mapper=colors['transform'], width=8, location=(0, 0), title=labeldict[cstr])

        fig.add_layout(color_bar, 'right')

    else:
        x_errcoords, y_errcoords, empty_x, empty_y = errors_from_coords(star_props[xstr], star_props[ystr], star_props[xstr + "_errs"], star_props[ystr + "_errs"])

        fig.multi_line(x_errcoords, empty_y)
        fig.multi_line(empty_x, y_errcoords)

        fig.scatter(source=starsource,
                    name="main",
                    x=xstr,
                    y=ystr,
                    radius=.015,
                    marker="circle",
                    alpha=.7, )

    # fig.circle(x=xstr, y=ystr, source=starsource, size=5)

    x = star_props[xstr][np.where(star_props[xstr] != -1000)]
    y = star_props[ystr][np.where(star_props[ystr] != -1000)]

    fig.x_range = Range1d(np.amin(x) - np.ptp(x) * 0.05, np.amax(x) + np.ptp(x) * 0.05)
    fig.y_range = Range1d(np.amin(y) - np.ptp(y) * 0.05, np.amax(y) + np.ptp(y) * 0.05)

    if ystr == "mag":
        fig.y_range = Range1d(np.amax(y) + np.ptp(y) * 0.05, np.amin(y) - np.ptp(y) * 0.05)
    if xstr == "mag":
        fig.x_range = Range1d(np.amax(x) + np.ptp(x) * 0.05, np.amin(x) - np.ptp(x) * 0.05)

    fig.toolbar.logo = None

    fig.yaxis.axis_label = labeldict[ystr]
    fig.xaxis.axis_label = labeldict[xstr]
    fig.yaxis.axis_label_text_font_size = '10pt'
    fig.xaxis.axis_label_text_font_size = '10pt'
    fig.min_border = 5

    return fig
