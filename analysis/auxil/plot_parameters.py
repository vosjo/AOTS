
import numpy as np

from bokeh import plotting as bpl
from bokeh import models as mpl

from stars.models import Star
from analysis.models import Parameter

from scipy.stats.stats import pearsonr

def plot_errorbars(fig, x, y, xerr=None, yerr=None, **kwargs):
   """
   Plot errorbars on a bokeh plot
   """
   
   if xerr != None:
      err_xs, err_ys = [], []
      for x_, y_, err in zip(x, y, xerr):
         err_xs.append((x_ - err, x_ + err))
         err_ys.append((y_, y_))
      fig.multi_line(err_xs, err_ys, **kwargs)
   
   if yerr != None:
      err_xs, err_ys = [], []
      for x_, y_, err in zip(x, y, yerr):
         err_xs.append((x_, x_))
         err_ys.append((y_ - err, y_ + err))
      fig.multi_line(err_xs, err_ys, **kwargs)
   
def get_data(parameters):
   """
   Returns array with data for the requested parameters
   """
   
   pnames = set(parameters.values())
   pnames.discard('')
   
   print( pnames )
   params = Parameter.objects.filter(cname__in=pnames, average=True)
   print( params )
   stars = params.values_list('star', flat=True).distinct()
   print( stars )
   stars = Star.objects.filter(pk__in=stars)
   
   #-- get the parameter values
   parameter_table = {'system': [s.name for s in stars]}
   for pname in pnames:
      values, errors = [], []
      for star in stars:
         try:
            print( pname, star.name )
            p = params.get(cname__exact=pname, star__exact=star.pk, average__exact=True)
            values.append(p.value)
            errors.append(p.error)
         except Parameter.DoesNotExist:
            values.append(np.nan)
            errors.append(np.nan)
      parameter_table[pname] = values
      parameter_table['e_'+pname] = errors
   
   #dtypes = [('system', 'a50')] + [(str(p), 'f8') for p in pnames]
   #parameter_table = np.core.records.fromarrays(parameter_table, dtype=dtypes)
   
   print( parameter_table )
   
   return parameter_table, list(pnames)

def get_parameter_statistics(data, parameters):
   
   try:
      p1 = parameters[0]
      p2 = parameters[1]
      
      corr, pvalue = pearsonr(data[p1], data[p2])
      
      return "Pearson correlation ({} - {}) = {:0.2f},   P-value = {:0.3f}".format(p1,
                                                                     p2, corr, pvalue)
   except Exception:
      return "No statistics calculated"

def plot_parameters(parameters, **kwargs):
   """
   Makes a simple plot of the given parameters
   """
   xpar = parameters.get('xaxis', 'p')
   ypar = parameters.get('yaxis', 'e')
   
   
   data, parameters = get_data(parameters)
   statistics = get_parameter_statistics(data, parameters)
   
   #-- datasource for bokeh
   datasource = bpl.ColumnDataSource(data=data)
   
   
   tooltips = [('System', '@system')] + \
              [(p, '@{} +- @e_{}'.format(p, p)) for p in parameters]
   hover = mpl.HoverTool(tooltips=tooltips)
   
   TOOLS = [mpl.PanTool(), mpl.WheelZoomTool(), 
            mpl.BoxZoomTool(), mpl.ResetTool(), hover]
   
   fig = bpl.figure(plot_width=800, plot_height=600, toolbar_location='right',
                    tools=TOOLS)
   
   fig.circle(xpar, ypar, source=datasource, size=5)
   #    Make sure xpar is filled otherwise avoid plotting
   if xpar != '':
      plot_errorbars(fig, data[xpar], data[ypar], xerr = data['e_'+xpar], yerr = data['e_'+ypar])
   
   fig.toolbar.logo=None
   fig.yaxis.axis_label = ypar
   fig.xaxis.axis_label = xpar
   fig.yaxis.axis_label_text_font_size = '10pt'
   fig.xaxis.axis_label_text_font_size = '10pt'
   fig.min_border = 5
   
   return fig, statistics
