"""
collection of all necessary bokeh plotting functions for analysis methods
"""

import h5py
import numpy as np
from bokeh import models as mpl
from bokeh import plotting as bpl

from dash.bokeh_theme import (
    apply_bokeh_figure_theme,
    resolve_bokeh_theme,
    themed_field_hover_tool,
    themed_status_label,
)


def _finish_figure(fig, theme):
    apply_bokeh_figure_theme(fig, resolve_bokeh_theme(theme))
    return fig


def _finish_figures(figures, theme):
    plot_theme = resolve_bokeh_theme(theme)
    for fig in figures.values():
        apply_bokeh_figure_theme(fig, plot_theme)
    return figures


def plot_errorbars(fig, x, y, e, **kwargs):
    """
    Plot errorbars on a bokeh plot
    """
    err_xs, err_ys = [], []
    for x, y, yerr in zip(x, y, e):
        err_xs.append((x, x))
        err_ys.append((y - yerr, y + yerr))
    fig.multi_line(err_xs, err_ys, **kwargs)


def get_attr(dataset, attr, default=None):
    """
    Function necessary to deal with the weird bytes storages of strings in hdf5s
    """
    if not dataset.attrs.__contains__(attr):
        return default

    attr = dataset.attrs.get(attr)
    if type(attr) == bytes:
        return attr.decode("ascii")
    else:
        return attr


def plot_generic(datafile, *, theme=None):
    """
    Generic plotting interface
    will plot the data and models as lines or circles/square.
    """
    hdf = h5py.File(datafile, "r")

    xscale = (
        get_attr(hdf["DATA"], "xscale", default="linear") if "DATA" in hdf else "linear"
    )
    yscale = (
        get_attr(hdf["DATA"], "yscale", default="linear") if "DATA" in hdf else "linear"
    )

    fig = bpl.figure(
        width=600,
        height=400,
        sizing_mode='scale_width',
        toolbar_location=None,
        x_axis_type=xscale,
        y_axis_type=yscale,
    )
    colors = ["red", "blue", "green"]

    def plot(data, mode="DATA"):
        for i, (name, dataset) in enumerate(data.items()):
            xpar = get_attr(dataset, "xpar", "x")
            ypar = get_attr(dataset, "ypar", "y")

            lim = [
                get_attr(dataset, "xmin", -np.inf),
                get_attr(dataset, "xmax", +np.inf),
            ]
            s = np.where((dataset[xpar] > lim[0]) & (dataset[xpar] < lim[1]))

            if get_attr(dataset, "datatype", None) == "continuous":
                line_dash = "dashed" if mode == "DATA" else "solid"
                fig.line(
                    dataset[xpar][s],
                    dataset[ypar][s],
                    color=colors[i],
                    line_dash=line_dash,
                    legend_label=name,
                )

            elif get_attr(dataset, "datatype", None) == "discrete" and mode == "DATA":
                fig.scatter(
                    dataset[xpar][s],
                    dataset[ypar][s],
                    marker="circle",
                    color=colors[i],
                    legend_label=name,
                    size=6,
                )

            elif get_attr(dataset, "datatype", None) == "discrete" and mode == "MODEL":
                fig.x(
                    dataset[xpar][s],
                    dataset[ypar][s],
                    color=colors[i],
                    legend_label=name,
                )

            if ypar + "_err" in dataset.dtype.names:
                plot_errorbars(
                    fig,
                    dataset[xpar],
                    dataset[ypar],
                    dataset[ypar + "_err"],
                    color=colors[i],
                )

    # -- plot the data
    if "DATA" in hdf:
        data = hdf["DATA"]
        plot(data, mode="DATA")

    # -- plot the models
    if "MODEL" in hdf:
        data = hdf["MODEL"]
        plot(data, mode="MODEL")

    fig.toolbar.logo = None
    fig.yaxis.axis_label = get_attr(data, "ylabel", "y")
    fig.xaxis.axis_label = get_attr(data, "xlabel", "x")
    fig.yaxis.axis_label_text_font_size = "10pt"
    fig.xaxis.axis_label_text_font_size = "10pt"
    fig.min_border = 5

    hdf.close()

    return _finish_figure(fig, theme)


def plot_generic_large(datafile, *, theme=None):
    """
    Generic plotting interface
    will plot the data and models as lines or circles/square.
    """
    hdf = h5py.File(datafile, "r")

    TOOLS = "pan, box_zoom, wheel_zoom, reset"

    xscale = (
        get_attr(hdf["DATA"], "xscale", default="linear") if "DATA" in hdf else "linear"
    )
    yscale = (
        get_attr(hdf["DATA"], "yscale", default="linear") if "DATA" in hdf else "linear"
    )

    fig = bpl.figure(
        width=800,
        height=500,
        sizing_mode='scale_width',
        toolbar_location="right",
        tools=TOOLS,
        x_axis_type=xscale,
        y_axis_type=yscale,
    )
    colors = ["red", "blue", "green"]

    # -- plot the data
    if "DATA" in hdf:
        data = hdf["DATA"]

        for i, (name, dataset) in enumerate(data.items()):
            xpar = get_attr(dataset, "xpar", "x")
            ypar = get_attr(dataset, "ypar", "y")

            # we might evenutally need this to convert bytes crap from hdf5 to string
            # datatable = astropy.io.misc.hdf5.read_table_hdf5(dataset, path=None, character_as_bytes=False)

            if get_attr(dataset, "datatype", None) == "continuous":
                fig.line(
                    dataset[xpar],
                    dataset[ypar],
                    color=colors[i],
                    line_dash="dashed",
                    legend_label=name,
                )

            elif get_attr(dataset, "datatype", None) == "discrete":
                # Each discrete series needs its own source: Bokeh requires equal column lengths.
                bokehsource = bpl.ColumnDataSource({
                    name + "_x": dataset[xpar],
                    name + "_y": dataset[ypar],
                })
                if ypar + "_err" in dataset.dtype.names:
                    bokehsource.data[name + "_yerr"] = dataset[ypar + "_err"]

                rend = fig.scatter(
                    name + "_x",
                    name + "_y",
                    marker="circle",
                    color=colors[i],
                    source=bokehsource,
                    size=7,
                    legend_label=name,
                )

                tooltips = [(get_attr(data, "xlabel", "x"), "@" + name + "_x")]
                if ypar + "_err" in dataset.dtype.names:
                    tooltips += [
                        (
                            get_attr(data, "ylabel", "y"),
                            "@" + name + "_y +- @" + name + "_yerr",
                        )
                    ]

                    plot_errorbars(
                        fig,
                        dataset[xpar],
                        dataset[ypar],
                        dataset[ypar + "_err"],
                        line_width=1,
                        color=colors[i],
                    )
                else:
                    tooltips += [(get_attr(data, "ylabel", "y"), "@" + name + "_y")]

                hover_tool = themed_field_hover_tool(
                    renderers=[rend],
                    tooltips=tooltips,
                    theme=resolve_bokeh_theme(theme),
                )
                fig.add_tools(hover_tool)

    # -- plot the models
    if "MODEL" in hdf:
        models = hdf["MODEL"]
        for i, (name, dataset) in enumerate(models.items()):
            xpar = get_attr(dataset, "xpar", "x")
            ypar = get_attr(dataset, "ypar", "y")

            if get_attr(dataset, "datatype", None) == "continuous":
                fig.line(
                    dataset[xpar], dataset[ypar], color=colors[i], legend_label=name
                )
            elif get_attr(dataset, "datatype", None) == "discrete":
                fig.x(
                    dataset[xpar],
                    dataset[ypar],
                    color=colors[i],
                    legend_label=name,
                    size=10,
                )

    fig.toolbar.logo = None
    fig.yaxis.axis_label = get_attr(data, "ylabel", "y")
    fig.xaxis.axis_label = get_attr(data, "xlabel", "x")
    fig.yaxis.axis_label_text_font_size = "10pt"
    fig.xaxis.axis_label_text_font_size = "10pt"
    fig.min_border = 5

    hdf.close()

    # from bokeh.models import Button, CustomJS
    # button = Button(label='fullscreen')
    # button.callback = CustomJS(args=dict(fig=fig), code="""
    # var old_width = fig.width;
    # var doc = fig.document;
    # fig.width = old_width * 0.8;
    # doc.resize();
    # """)
    # http://stackoverflow.com/questions/39972162/dynamically-change-the-shape-of-bokeh-figure

    return _finish_figure(fig, theme)  # , button


def plot_generic_OC(datafile, *, theme=None):
    hdf = h5py.File(datafile, "r")

    TOOLS = "pan, box_zoom, wheel_zoom, reset"

    xscale = (
        get_attr(hdf["O-C"], "xscale", default="linear") if "O-C" in hdf else "linear"
    )
    yscale = (
        get_attr(hdf["O-C"], "yscale", default="linear") if "O-C" in hdf else "linear"
    )

    fig = bpl.figure(
        width=800,
        height=200,
        sizing_mode='scale_width',
        toolbar_location="right",
        tools=TOOLS,
        x_axis_type=xscale,
        y_axis_type=yscale,
    )
    colors = ["red", "blue", "green"]

    # -- plot the O-C

    if "O-C" in hdf:
        models = hdf["O-C"]
        for i, (name, dataset) in enumerate(models.items()):
            xpar = get_attr(dataset, "xpar", "x")
            ypar = get_attr(dataset, "ypar", "y")

            if get_attr(dataset, "datatype", None) == "continuous":
                fig.line(
                    dataset[xpar], dataset[ypar], color=colors[i], legend_label=name
                )
            elif get_attr(dataset, "datatype", None) == "discrete":
                fig.scatter(
                    dataset[xpar],
                    dataset[ypar],
                    marker="circle",
                    color=colors[i],
                    legend_label=name,
                    size=7,
                )

                plot_errorbars(
                    fig,
                    dataset[xpar],
                    dataset[ypar],
                    dataset[ypar + "_err"],
                    line_width=1,
                    color=colors[i],
                )

        hline = mpl.Span(
            location=0,
            dimension="width",
            line_color=resolve_bokeh_theme(theme).outline,
            line_width=2,
            line_dash="dashed",
        )
        fig.add_layout(hline)

        fig.yaxis.axis_label = get_attr(models, "ylabel", "y")
        fig.xaxis.axis_label = get_attr(models, "xlabel", "x")

    else:
        plot_theme = resolve_bokeh_theme(theme)
        error_text = themed_status_label(
            x=400,
            y=100,
            x_units="screen",
            y_units="screen",
            text="No O-C data available.",
            theme=plot_theme,
        )

        fig.add_layout(error_text)

    fig.toolbar.logo = None
    fig.yaxis.axis_label_text_font_size = "10pt"
    fig.xaxis.axis_label_text_font_size = "10pt"
    fig.min_border = 5

    hdf.close()

    return _finish_figure(fig, theme)


def plot_generic_hist(datafile, *, theme=None):
    hdf = h5py.File(datafile, "r")

    figures = {}

    if not "PARAMETERS" in hdf:
        hdf.close()
        return figures

    data = hdf["PARAMETERS"]
    for i, (name, dataset) in enumerate(data.items()):
        if "DISTRIBUTION" in dataset:
            err = dataset.attrs.get("err", 0.0)
            emin = dataset.attrs.get("emin", err)
            emax = dataset.attrs.get("emax", err)
            value = dataset.attrs.get("value", 0.0)

            title = "{} = {:.2f} + {:.2f} - {:.2f}".format(name, value, emax, emin)

            fig = bpl.figure(
                width=280, height=280, sizing_mode='scale_width', tools=[], title=title,
            )

            xpar = get_attr(dataset, "xpar", "x")
            ypar = get_attr(dataset, "ypar", "y")

            x = dataset["DISTRIBUTION"][xpar]
            y = dataset["DISTRIBUTION"][ypar]
            width = np.average(x[1:] - x[0:-1])

            fig.vbar(x=x, width=width, bottom=0, top=y, color="black", fill_alpha=0)

            best = mpl.Span(
                location=value,
                dimension="height",
                line_color="red",
                line_width=2,
                line_dash="solid",
            )
            minv = mpl.Span(
                location=value - emin,
                dimension="height",
                line_color="red",
                line_width=2,
                line_dash="dashed",
            )
            maxv = mpl.Span(
                location=value + emin,
                dimension="height",
                line_color="red",
                line_width=2,
                line_dash="dashed",
            )
            fig.renderers.extend([best, minv, maxv])

            fig.min_border = 10
            fig.min_border_top = 1
            fig.min_border_bottom = 40
            fig.toolbar.logo = None
            fig.toolbar_location = None
            fig.title.align = "center"

            figures[name] = fig

    hdf.close()

    return _finish_figures(figures, theme)


def plot_generic_ci(datafile, *, theme=None):
    hdf = h5py.File(datafile, "r")

    figures = {}

    if not "PARAMETERS" in hdf:
        hdf.close()
        return figures

    data = hdf["PARAMETERS"]
    for i, (name, dataset) in enumerate(data.items()):
        if "Chi2Val" in dataset:
            err = dataset.attrs.get("err", 0.0)
            emin = dataset.attrs.get("emin", err)
            emax = dataset.attrs.get("emax", err)
            value = dataset.attrs.get("value", 0.0)

            title = "{} = {:.2f} + {:.2f} - {:.2f}".format(name, value, emax, emin)

            fig = bpl.figure(
                width=280, height=280, sizing_mode='scale_width', tools=[], title=title,
            )

            fig.ray(
                x=dataset["Chi2Val"]["x"],
                y=dataset["Chi2Val"]["y"],
                length=0,
                angle=np.pi / 2.0,
                line_width=3,
            )

            fig.line(
                dataset["Chi2Fit"]["x"],
                dataset["Chi2Fit"]["y"],
                line_width=1,
                color="red",
                alpha=0.7,
            )

            min_chi2 = np.min(dataset["Chi2Val"]["y"])
            fig.y_range = mpl.Range1d(0.85 * min_chi2, 1.25 * min_chi2)

            fig.min_border = 10
            fig.min_border_top = 1
            fig.min_border_bottom = 40
            fig.toolbar.logo = None
            fig.toolbar_location = None
            fig.title.align = "center"

            figures[name] = fig

    hdf.close()

    return _finish_figures(figures, theme)


# ============================================================================================
# Error plots (empty plot in case an exception is thrown
# ============================================================================================


def plot_error(width, height, *, theme=None):
    fig = bpl.figure(
        width=width, height=height, sizing_mode='scale_width', toolbar_location=None,
    )

    plot_theme = resolve_bokeh_theme(theme)
    error_text = themed_status_label(
        x=width / 2.0,
        y=height / 2.0,
        x_units="screen",
        y_units="screen",
        text="An error occured when trying to plot this dataset!",
        theme=plot_theme,
    )

    fig.add_layout(error_text)

    return _finish_figure(fig, theme)


def plot_error_large(*, theme=None):
    fig = bpl.figure(
        width=800, height=500, sizing_mode='scale_width', toolbar_location=None,
    )

    plot_theme = resolve_bokeh_theme(theme)
    error_text = themed_status_label(
        x=400,
        y=250,
        x_units="screen",
        y_units="screen",
        text="An error occured when trying to plot this dataset!",
        theme=plot_theme,
    )

    fig.add_layout(error_text)

    return _finish_figure(fig, theme)


import traceback


def plot_analysis(datafile, category=None, *, theme=None):
    """
    General plotting function for analysis
    """
    try:
        return plot_generic(datafile, theme=theme)
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        return plot_error(600, 400, theme=theme)


def plot_analysis_large(datafile, category=None, *, theme=None):
    """
    General plotting function for analysis, makes the large version plot for
    the detail pages including extra info when hovering over a figure
    """
    try:
        return plot_generic_large(datafile, theme=theme)
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        return plot_error_large(theme=theme)


def plot_analysis_oc(datafile, category=None, *, theme=None):
    try:
        return plot_generic_OC(datafile, theme=theme)
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        return plot_error(800, 200, theme=theme)


def plot_parameter_ci(datafile, category=None, *, theme=None):
    """
    General plotting function for the confidence intervals of the parameters.
    This will return a figure for each confidence interval (1D) that is included
    in the datafile
    """

    try:
        return plot_generic_ci(datafile, theme=theme)
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        return plot_error(280, 280, theme=theme)
