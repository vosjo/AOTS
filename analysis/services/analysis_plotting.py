from analysis.auxil import plot_analyses


def plot_analysis_figure(analysis):
    return plot_analyses.plot_analysis(analysis.datafile.path, analysis.category)


def plot_analysis_large(analysis):
    return plot_analyses.plot_analysis_large(analysis.datafile.path, analysis.category)


def plot_analysis_oc(analysis):
    return plot_analyses.plot_analysis_oc(analysis.datafile.path, analysis.category)


def plot_parameter_histograms(analysis):
    return plot_analyses.plot_generic_hist(analysis.datafile.path)


def plot_parameter_ci(analysis):
    return plot_analyses.plot_parameter_ci(analysis.datafile.path, analysis.category)


def plot_analysis_detail_figures(analysis):
    """Fit, O-C, and histogram figures for analysis detail views."""
    fit = plot_analysis_large(analysis)
    oc = plot_analysis_oc(analysis)
    hist = plot_parameter_histograms(analysis)
    return dict(hist, **{'fit': fit, 'oc': oc})
