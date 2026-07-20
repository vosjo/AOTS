"""
collection of all necessary bokeh plotting functions for analysis methods
"""

import h5py
import numpy as np
from bokeh import models as mpl
from bokeh import plotting as bpl

from analysis.auxil.plot_axis_labels import resolve_axis_labels
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


def _resolve_model_group(hdf, fit_id=None):
    """Return MODEL group from root or from FITS/<fit_id>/ for multi-fit v2."""
    if 'FITS' in hdf and len(hdf['FITS']) > 0:
        chosen = fit_id
        if not chosen or chosen not in hdf['FITS']:
            chosen = hdf.attrs.get('best_fit_id')
            if isinstance(chosen, bytes):
                chosen = chosen.decode('utf-8', errors='replace')
        if chosen and chosen in hdf['FITS'] and 'MODEL' in hdf['FITS'][chosen]:
            return hdf['FITS'][chosen]['MODEL']
        for fid in hdf['FITS']:
            if 'MODEL' in hdf['FITS'][fid]:
                return hdf['FITS'][fid]['MODEL']
    if 'MODEL' in hdf:
        return hdf['MODEL']
    return None


def plot_generic(datafile, *, theme=None, category=None, fit_id=None):
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

    x_label, y_label = resolve_axis_labels(hdf, category=category)

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
                fig.scatter(
                    dataset[xpar][s],
                    dataset[ypar][s],
                    marker="x",
                    color=colors[i],
                    legend_label=name,
                    size=8,
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

    # -- plot the models (root MODEL or FITS/<id>/MODEL for multi-fit v2)
    models = _resolve_model_group(hdf, fit_id=fit_id)
    if models is not None:
        plot(models, mode="MODEL")

    fig.toolbar.logo = None
    fig.yaxis.axis_label = y_label
    fig.xaxis.axis_label = x_label
    fig.yaxis.axis_label_text_font_size = "10pt"
    fig.xaxis.axis_label_text_font_size = "10pt"
    fig.min_border = 5

    hdf.close()

    return _finish_figure(fig, theme)


def plot_generic_large(datafile, *, theme=None, category=None, fit_id=None):
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

    x_label, y_label = resolve_axis_labels(hdf, category=category)

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
            legend = get_attr(dataset, 'label', None) or name

            # we might evenutally need this to convert bytes crap from hdf5 to string
            # datatable = astropy.io.misc.hdf5.read_table_hdf5(dataset, path=None, character_as_bytes=False)

            if get_attr(dataset, "datatype", None) == "continuous":
                fig.line(
                    dataset[xpar],
                    dataset[ypar],
                    color=colors[i],
                    line_dash="dashed",
                    legend_label=legend,
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

                tooltips = [(x_label, "@" + name + "_x")]
                if ypar + "_err" in dataset.dtype.names:
                    tooltips += [
                        (
                            y_label,
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
                    tooltips += [(y_label, "@" + name + "_y")]

                hover_tool = themed_field_hover_tool(
                    renderers=[rend],
                    tooltips=tooltips,
                    theme=resolve_bokeh_theme(theme),
                )
                fig.add_tools(hover_tool)

    # -- plot the models (root MODEL or FITS/<id>/MODEL for multi-fit v2)
    models = _resolve_model_group(hdf, fit_id=fit_id)
    if models is not None:
        for i, (name, dataset) in enumerate(models.items()):
            xpar = get_attr(dataset, "xpar", "x")
            ypar = get_attr(dataset, "ypar", "y")

            legend = get_attr(dataset, 'label', None) or name
            if get_attr(dataset, "datatype", None) == "continuous":
                fig.line(
                    dataset[xpar], dataset[ypar], color=colors[i], legend_label=legend
                )
            elif get_attr(dataset, "datatype", None) == "discrete":
                fig.scatter(
                    dataset[xpar],
                    dataset[ypar],
                    marker="x",
                    color=colors[i],
                    legend_label=legend,
                    size=10,
                )

    fig.toolbar.logo = None
    fig.yaxis.axis_label = y_label
    fig.xaxis.axis_label = x_label
    fig.yaxis.axis_label_text_font_size = "10pt"
    fig.xaxis.axis_label_text_font_size = "10pt"
    fig.min_border = 5

    hdf.close()

    return _finish_figure(fig, theme)  # , button


def plot_generic_OC(datafile, *, theme=None, category=None, fit_id=None):
    hdf = h5py.File(datafile, "r")

    TOOLS = "pan, box_zoom, wheel_zoom, reset"

    oc_group = None
    if fit_id and "FITS" in hdf and fit_id in hdf["FITS"] and "O-C" in hdf["FITS"][fit_id]:
        oc_group = hdf["FITS"][fit_id]["O-C"]
    elif "O-C" in hdf:
        oc_group = hdf["O-C"]

    xscale = get_attr(oc_group, "xscale", default="linear") if oc_group is not None else "linear"
    yscale = get_attr(oc_group, "yscale", default="linear") if oc_group is not None else "linear"

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

    if oc_group is not None:
        models = oc_group
        for i, (name, dataset) in enumerate(models.items()):
            xpar = get_attr(dataset, "xpar", "x")
            ypar = get_attr(dataset, "ypar", "y")
            legend = get_attr(dataset, 'label', None) or name

            if get_attr(dataset, "datatype", None) == "continuous":
                fig.line(
                    dataset[xpar], dataset[ypar], color=colors[i], legend_label=legend
                )
            elif get_attr(dataset, "datatype", None) == "discrete":
                fig.scatter(
                    dataset[xpar],
                    dataset[ypar],
                    marker="circle",
                    color=colors[i],
                    legend_label=legend,
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

        oc_x, oc_y = resolve_axis_labels(hdf, category=category)
        fig.yaxis.axis_label = oc_y
        fig.xaxis.axis_label = oc_x

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


def plot_rv_curve(datafile, *, theme=None, fit_id=None, large=False, category=None):
    """Plot RV measurements and optional model curve from v2 or legacy layout."""
    from analysis.auxil.fileio import read2dict
    from analysis.auxil.rv_hdf5 import get_best_fit_id, get_measurements_table, is_rv_curve_v2, list_rv_fits

    data = read2dict(datafile)
    fit_id = fit_id or get_best_fit_id(data)

    width = 800 if large else 600
    height = 500 if large else 400
    fig_kwargs = dict(
        width=width,
        height=height,
        sizing_mode='scale_width',
        toolbar_location='right' if large else None,
    )
    if large:
        fig_kwargs['tools'] = 'pan, box_zoom, wheel_zoom, reset'
    fig = bpl.figure(**fig_kwargs)

    if is_rv_curve_v2(data):
        mtable = get_measurements_table(data)
        if mtable is not None:
            x = mtable['time']
            y = mtable['rv']
            err = mtable.get('err_formal')
            fig.scatter(x, y, size=6, color='red', legend_label='Measurements')
            if err is not None:
                plot_errorbars(fig, x, y, err, color='red')

        if fit_id:
            fit_group = data.get('FITS', {}).get(fit_id, {})
            model = fit_group.get('MODEL') if isinstance(fit_group, dict) else None
            if isinstance(model, dict):
                for i, (name, dataset) in enumerate(model.items()):
                    if hasattr(dataset, 'dtype') and getattr(dataset.dtype, 'names', None):
                        names = dataset.dtype.names
                        xpar = 'time' if 'time' in names else names[0]
                        ypar = 'rv' if 'rv' in names else names[1]
                        fig.line(
                            dataset[xpar], dataset[ypar],
                            color=['blue', 'green', 'orange'][i % 3],
                            legend_label=name,
                        )
    else:
        return plot_generic_large(datafile, theme=theme, category=category) if large else plot_generic(datafile, theme=theme, category=category)

    fits = list_rv_fits(data)
    if fit_id and fits:
        label = next((f['label'] for f in fits if f['id'] == fit_id), fit_id)
        fig.title.text = f'RV curve — {label}'

    fig.xaxis.axis_label = 'Time'
    fig.yaxis.axis_label = 'RV (km/s)'
    return _finish_figure(fig, theme)


import traceback


def plot_analysis(datafile, category=None, *, theme=None, fit_id=None):
    """
    General plotting function for analysis
    """
    try:
        from analysis.categories import AnalysisCategory
        if category == AnalysisCategory.RV_CURVE:
            return plot_rv_curve(datafile, theme=theme, fit_id=fit_id, large=False, category=category)
        return plot_generic(datafile, theme=theme, category=category, fit_id=fit_id)
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        return plot_error(600, 400, theme=theme)


def plot_analysis_large(datafile, category=None, *, theme=None, fit_id=None):
    """
    General plotting function for analysis, makes the large version plot for
    the detail pages including extra info when hovering over a figure
    """
    try:
        from analysis.categories import AnalysisCategory
        if category == AnalysisCategory.RV_CURVE:
            return plot_rv_curve(datafile, theme=theme, fit_id=fit_id, large=True, category=category)
        return plot_generic_large(datafile, theme=theme, category=category, fit_id=fit_id)
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        return plot_error_large(theme=theme)


def plot_analysis_oc(datafile, category=None, *, theme=None, fit_id=None):
    try:
        return plot_generic_OC(datafile, theme=theme, category=category, fit_id=fit_id)
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
