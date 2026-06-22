from analysis.auxil import plot_analyses


def plot_analysis_figure(analysis, *, theme=None):
    return plot_analyses.plot_analysis(analysis.datafile.path, analysis.category, theme=theme)


def plot_analysis_large(analysis, *, theme=None):
    return plot_analyses.plot_analysis_large(analysis.datafile.path, analysis.category, theme=theme)


def plot_analysis_oc(analysis, *, theme=None):
    return plot_analyses.plot_analysis_oc(analysis.datafile.path, analysis.category, theme=theme)


def plot_parameter_histograms(analysis, *, theme=None):
    return plot_analyses.plot_generic_hist(analysis.datafile.path, theme=theme)


def plot_parameter_ci(analysis, *, theme=None):
    return plot_analyses.plot_parameter_ci(analysis.datafile.path, analysis.category, theme=theme)


def plot_analysis_detail_figures(analysis, *, theme=None):
    """Fit, O-C, and histogram figures for analysis detail views."""
    fit = plot_analysis_large(analysis, theme=theme)
    oc = plot_analysis_oc(analysis, theme=theme)
    hist = plot_parameter_histograms(analysis, theme=theme)
    return dict(hist, **{'fit': fit, 'oc': oc})
