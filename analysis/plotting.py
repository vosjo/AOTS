import numpy as np
from bokeh import models as mpl
from bokeh import plotting as bpl
from bokeh.palettes import Viridis9
from bokeh.models import widgets, ColorBar
from bokeh.transform import linear_cmap

from stars.models import Project, Star
from .labels import labeldict


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

    for star in star_list:
        pset = star.parameter_set.all()
        photset = star.photometry_set.all()
        try:
            magset = photset.filter(band__icontains='.G')
            mag = sum([m.measurement for m in magset])/len(magset)
            magerr = np.sqrt(sum([m.error**2 for m in magset])/len(magset))
        except ZeroDivisionError:
            mag = magerr = -1000.
        try:
            t = pset.filter(name__icontains='teff')
            teff = t.value
            tefferr = t.error
        except:
            teff = tefferr = -1000.
        try:
            l = pset.filter(name__icontains='log_g')
            logg = l.value
            loggerr = l.error
        except:
            logg = loggerr = -1000.
        try:
            b = pset.filter(name__icontains='bp_rp')
            assert len(b) > 0
            bp_rp = b.value
            bp_rp_err = b.error
            if bp_rp < -4:
                a = 4
        except AssertionError:
            try:
                bp = photset.filter(band__icontains=".BP")
                rp = photset.filter(band__icontains=".RP")

                bp_rp = bp[0].measurement-rp[0].measurement
                bp_rp_err = np.sqrt(bp[0].error**2+rp[0].error**2)
                if bp_rp < -4:
                    a = 4
            except IndexError:
                bp_rp = bp_rp_err = -1000.
                if bp_rp < -4:
                    a = 4

        mags.append(mag)
        mags_errs.append(magerr)
        teffs.append(teff)
        teffs_errs.append(tefferr)
        loggs.append(logg)
        loggs_errs.append(loggerr)
        bp_rps.append(bp_rp)
        bp_rps_errs.append(bp_rp_err)

    star_props = dict(teff=np.array(teffs),
                      logg=np.array(loggs),
                      mag=np.array(mags),
                      bp_rp=np.array(bp_rps))

    if cstr is not None:
        normcstr = star_props[cstr]
        if len(np.where(normcstr != -1000.)) == 0:
            cstr = None
        normcstr[np.where(normcstr == -1000.)] = np.mean(normcstr[np.where(normcstr != -1000.)])
        star_props["norm_"+cstr] = normcstr
    if rstr is not None:
        normrstr = star_props[rstr]
        if len(np.where(normrstr != -1000.)) == 0:
            rstr = None
        normrstr[np.where(normrstr == -1000.)] = np.mean(normrstr[np.where(normrstr != -1000.)])
        normrstr = normrstr/np.amax(normrstr)*.01
        star_props["norm_" + rstr] = normrstr
        
    starsource = bpl.ColumnDataSource(data=star_props)
    hover = mpl.HoverTool(tooltips=[("T_eff", "@teff"), ("log(g)", "@logg"), ("magnitude", "@mag")],
                          names=['hover'])

    tools = [mpl.PanTool(), mpl.WheelZoomTool(),
             mpl.BoxZoomTool(), mpl.ResetTool(), hover]
    fig = bpl.figure(plot_width=700, plot_height=400, tools=tools)

    # fig.circle(wave, meas)
    # fig.circle('bp_rp', 'mag', size=8, color='white', alpha=0.1, name='hover', source=starsource)

    if rstr is not None and cstr is not None:
        colors = linear_cmap("norm_"+cstr, palette=Viridis9, low=np.amin(normcstr),
                             high=np.amax(normcstr))

        fig.scatter(source=starsource,
                    x=xstr,
                    y=ystr,
                    radius="norm_"+rstr,
                    marker="circle",
                    alpha=.7,
                    fill_color=colors,
                    line_color=colors)

        color_bar = ColorBar(color_mapper=colors['transform'], width=8, location=(0, 0), title=labeldict[cstr])

        fig.add_layout(color_bar, 'right')

    elif rstr is not None:
        fig.scatter(source=starsource,
                    x=xstr,
                    y=ystr,
                    radius="norm_"+rstr,
                    marker="circle",
                    alpha=.7)

    elif cstr is not None:
        colors = linear_cmap("norm_"+cstr, palette=Viridis9, low=np.amin(star_props["norm_"+cstr]),
                             high=np.amax(star_props["norm_"+cstr]))

        fig.scatter(source=starsource,
                    x=xstr,
                    y=ystr,
                    marker="circle",
                    alpha=.7,
                    fill_color=colors,
                    line_color=colors)

        color_bar = ColorBar(color_mapper=colors['transform'], width=8, location=(0, 0), title=labeldict[cstr])

        fig.add_layout(color_bar, 'right')

    else:
        fig.scatter(source=starsource,
                    x=xstr,
                    y=ystr,
                    marker="circle",
                    alpha=.7,)

    # fig.circle(x=xstr, y=ystr, source=starsource, size=5)

    x = star_props[xstr][np.where(star_props[xstr] != -1000)]
    y = star_props[ystr][np.where(star_props[ystr] != -1000)]

    fig.x_range.start = np.amin(x)-np.ptp(x)*0.025
    fig.x_range.end = np.amax(x)+np.ptp(x)*0.025
    fig.y_range.start = np.amin(y)-np.ptp(y)*0.025
    fig.y_range.end = np.amax(y)+np.ptp(y)*0.025

    if ystr == "mag":
        fig.y_range.start = np.amax(y) + np.ptp(y) * 0.025
        fig.y_range.end = np.amin(y) - np.ptp(y) * 0.025
    if xstr == "mag":
        fig.x_range.start = np.amax(x) + np.ptp(x) * 0.025
        fig.x_range.end = np.amin(x) - np.ptp(x) * 0.025

    fig.toolbar.logo = None

    fig.yaxis.axis_label = labeldict[ystr]
    fig.xaxis.axis_label = labeldict[xstr]
    fig.yaxis.axis_label_text_font_size = '10pt'
    fig.xaxis.axis_label_text_font_size = '10pt'
    fig.min_border = 5




    return fig

