from astropy.io import fits
from bokeh import plotting as bpl
from scipy.interpolate import interp1d
import numpy as np
from analysis.auxil.plot_datasets import plot_error_large, plot_error
from bokeh import models as mpl


def plot_rvcurve(datafile):
    fitsfile = fits.open(datafile.path)

    if len(fitsfile) == 2:
        metadata = dict(fitsfile[0].header)
        datapoints = np.array(list(fitsfile[1].data))
        fit = None
    elif len(fitsfile) == 3:
        metadata = dict(fitsfile[0].header)
        datapoints = np.array(list(fitsfile[1].data))
        fit = fitsfile[2].data
    else:
        raise AssertionError("Your provided RVcurve file does not seem to match the requirements!")

    column_names = dict(fitsfile[1].header)["COLNAMES"].split(";")

    times = datapoints[:, column_names.index("MJD")]
    rvs = datapoints[:, column_names.index("RV")]
    rvs_err = datapoints[:, column_names.index("RVERR")]

    TOOLS = "pan, box_zoom, wheel_zoom, reset"

    fig = bpl.figure(width=800, height=500, toolbar_location='right',
                     tools=TOOLS)

    fig.circle(times, rvs, color="blue",
               size=7, legend_label="")

    err_xs, err_ys = [], []
    for x, y, yerr in zip(times, rvs, rvs_err):
        err_xs.append((x, x))
        err_ys.append((y - yerr, y + yerr))
    fig.multi_line(err_xs, err_ys, color="blue")

    # tooltips = [(get_attr(data, 'xlabel', 'x'), "@" + name + "_x")]
    #
    # hover_tool = mpl.HoverTool(renderers=[rend], tooltips=tooltips)
    # fig.add_tools(hover_tool)

    fig.toolbar.logo = None
    fig.yaxis.axis_label = "RV (km/s)"
    fig.xaxis.axis_label = "HJD"
    fig.yaxis.axis_label_text_font_size = '10pt'
    fig.xaxis.axis_label_text_font_size = '10pt'
    fig.min_border = 5

    if fit:
        fittimes = fit[0, :]
        fitrvs = fit[1, :]

        ocfig = bpl.figure(width=800, height=200, toolbar_location='right',
                           tools=TOOLS)

        f = interp1d(fittimes, fitrvs, bounds_error=False)

        ocfig.circle(times, rvs-f(times), color="blue",
                     size=7, legend_label="")

    else:
        ocfig = bpl.figure(width=800, height=200)

        error_text = mpl.Label(x=400, y=100, x_units='screen', y_units='screen',
                               text='No O-C data available.',
                               text_color='red', text_align='center')

        ocfig.add_layout(error_text)

    return fig, ocfig, metadata


def plot_rvcurve_wrapper(datafile, method):
    """
    General plotting function for analysis, makes the large version plot for
    the detail pages including extra info when hovering over a figure
    """
    try:
        return plot_rvcurve(datafile)
    except Exception as e:
        print(e)
        return plot_error_large(), plot_error(800, 200)
