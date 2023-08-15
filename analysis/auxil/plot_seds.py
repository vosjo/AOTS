from astropy.io import fits
from bokeh import plotting as bpl
from scipy.interpolate import interp1d
import numpy as np
from analysis.auxil.plot_datasets import plot_error_large, plot_error
from bokeh import models as mpl
import copy


def plot_sed(datafile):
    fitsfile = fits.open(datafile.path)

    if len(fitsfile) == 2:
        metadata = dict(fitsfile[0].header)
        obs_datapoints = np.array(list(fitsfile[1].data))
        obs_info = dict(fitsfile[1].header)
        model_info = None
        model_data = None
    elif len(fitsfile) == 3:
        metadata = dict(fitsfile[0].header)
        obs_datapoints = np.array(list(fitsfile[1].data))
        obs_info = dict(fitsfile[1].header)
        model_data = np.array(list(fitsfile[2].data))
        model_info = dict(fitsfile[2].header)
    else:
        raise AssertionError("Your provided SED file does not seem to match the requirements!")

    obs_column_names = []
    n = 1
    while True:
        if "TTYPE" + str(n) in obs_info:
            obs_column_names.append(obs_info["TTYPE" + str(n)])
            n += 1
        else:
            break

    obs_wls = obs_datapoints[:, obs_column_names.index("Observed_Wavelength")]
    obs_flx = obs_datapoints[:, obs_column_names.index("Observed_Flux")]
    obs_mag = obs_datapoints[:, obs_column_names.index("Observed_Magnitude")]
    obs_flx_lerr = obs_datapoints[:, obs_column_names.index("Observed_Flux_Lower_Err")]
    obs_flx_uerr = obs_datapoints[:, obs_column_names.index("Observed_Flux_Upper_Err")]
    obs_mag_lerr = obs_datapoints[:, obs_column_names.index("Observed_Magnitude_Lower_Err")]
    obs_mag_uerr = obs_datapoints[:, obs_column_names.index("Observed_Magnitude_Upper_Err")]

    if model_info:
        model_column_names = []
        n = 1
        while True:
            if "TTYPE" + str(n) in model_info:
                model_column_names.append(model_info["TTYPE" + str(n)])
                n += 1
            else:
                break

    if model_info:
        mod_wls = model_data[:, model_column_names.index("Model_Wavelength")]
        mod_flx = model_data[:, model_column_names.index("Model_Flux")]
        mod_mag = model_data[:, model_column_names.index("Model_Magnitude")]
    else:
        mod_wls = None
        mod_flx = None
        mod_mag = None

    TOOLS = "pan, box_zoom, wheel_zoom, reset"
    flxfig = bpl.figure(width=800, height=500, toolbar_location='right',
                        tools=TOOLS)
    flx_ocfig = bpl.figure(width=800, height=200, toolbar_location='right',
                           tools=TOOLS)
    magfig = bpl.figure(width=800, height=500, toolbar_location='right',
                        tools=TOOLS)
    mag_ocfig = bpl.figure(width=800, height=200, toolbar_location='right',
                           tools=TOOLS)

    i = 0
    for datapoint, lerr, uerr, mod_datapoint, fig, ocfig in [
        (obs_flx, obs_flx_lerr, obs_flx_uerr, mod_flx, flxfig, flx_ocfig),
        (obs_mag, obs_mag_lerr, obs_mag_uerr, mod_mag, magfig, mag_ocfig)
    ]:
        print(i)
        if model_info:
            fig.line(mod_wls, mod_datapoint, legend_label="Model", color="darkgrey")
            f = interp1d(mod_wls, mod_datapoint, bounds_error=False)

            ocfig.circle(obs_wls, datapoint - f(obs_wls), color="blue",
                         size=7, legend_label="Residuals")

            err_xs, err_ys = [], []
            for x, y, y_lerr, y_uerr in zip(obs_wls, datapoint - f(obs_wls), lerr, uerr):
                err_xs.append((x, x))
                err_ys.append((y - y_lerr, y + y_uerr))
            ocfig.multi_line(err_xs, err_ys, color="blue")
            hline = mpl.Span(location=0, dimension='width', line_color='black', line_width=2, line_dash='dashed')
            ocfig.add_layout(hline)
            ocfig.toolbar.logo = None
            ocfig.yaxis.axis_label = ["Flux", "Magnitude"][i]
            ocfig.xaxis.axis_label = "Wavelength [Å]"
            ocfig.yaxis.axis_label_text_font_size = '10pt'
            ocfig.xaxis.axis_label_text_font_size = '10pt'
            ocfig.min_border = 5

        else:
            ocfig = bpl.figure(width=800, height=200)

            error_text = mpl.Label(x=400, y=100, x_units='screen', y_units='screen',
                                   text='No O-C data available.',
                                   text_color='red', text_align='center')

            ocfig.add_layout(error_text)

        fig.circle(obs_wls, datapoint, color="blue",
                   size=7, legend_label="Measurements")

        err_xs, err_ys = [], []
        for x, y, y_lerr, y_uerr in zip(obs_wls, datapoint, lerr, uerr):
            err_xs.append((x, x))
            err_ys.append((y - y_lerr, y + y_uerr))
        fig.multi_line(err_xs, err_ys, color="blue")

        # tooltips = [(get_attr(data, 'xlabel', 'x'), "@" + name + "_x")]
        #
        # hover_tool = mpl.HoverTool(renderers=[rend], tooltips=tooltips)
        # fig.add_tools(hover_tool)

        fig.toolbar.logo = None
        fig.yaxis.axis_label = ["Flux", "Magnitude"][i]
        fig.xaxis.axis_label = "Wavelength [Å]"
        fig.yaxis.axis_label_text_font_size = '10pt'
        fig.xaxis.axis_label_text_font_size = '10pt'
        fig.min_border = 5
        i += 1

    return flxfig, flx_ocfig, magfig, mag_ocfig, metadata


def plot_sed_wrapper(datafile, method):
    """
    General plotting function for analysis, makes the large version plot for
    the detail pages including extra info when hovering over a figure
    """
    try:
        return plot_sed(datafile)
    except Exception as e:
        print(e)
        return plot_error_large(), plot_error(800, 200)
