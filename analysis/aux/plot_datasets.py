 
""" 
collection of all necessary bokeh plotting functions for analysis methods
"""
import h5py

import numpy as np

from bokeh import plotting as bpl
from bokeh import models as mpl
from bokeh.models import widgets 

#from ivs.io import fileio
from analysis.aux import fileio
from analysis.aux.units import conversions

def plot_errorbars(fig, x, y, e, **kwargs):
   """
   Plot errorbars on a bokeh plot
   """
   err_xs, err_ys = [], []
   for x, y, yerr in zip(x, y, e):
      err_xs.append((x, x))
      err_ys.append((y - yerr, y + yerr))
   fig.multi_line(err_xs, err_ys, **kwargs)

def plot_generic(datafile):
   """
   Generic plotting interface
   will plot the data and models as lines or circles/square. 
   """
   hdf = h5py.File(datafile, 'r') 
   data = hdf['DATA']
   models = hdf['MODEL']
   
   
   fig = bpl.figure(plot_width=600, plot_height=400, responsive=False, toolbar_location=None)
   colors = ['red', 'blue', 'green']
   
   #-- plot the data
   for i, (name, dataset) in enumerate(data.items()):
      lim = [dataset.attrs.get('xmin', -np.inf), dataset.attrs.get('xmax', +np.inf)]
      s = np.where((dataset['x'] > lim[0]) & (dataset['x'] < lim[1]))
      
      if dataset.attrs.get('datatype', None) == 'continuous':
         fig.line(dataset['x'][s], dataset['y'][s], color=colors[i], line_dash='dashed', legend=name)
      elif dataset.attrs.get('datatype', None) == 'discrete':
         fig.circle(dataset['x'][s], dataset['y'][s], color=colors[i], legend=name)
      
      if 'yerr' in dataset.dtype.names:
         plot_errorbars(fig, dataset['x'], dataset['y'], dataset['yerr'], color=colors[i])
   
   #-- plot the models
   for i, (name, dataset) in enumerate(models.items()):
      lim = [dataset.attrs.get('xmin', -np.inf), dataset.attrs.get('xmax', +np.inf)]
      s = np.where((dataset['x'] > lim[0]) & (dataset['x'] < lim[1]))
      
      if dataset.attrs.get('datatype', None) == 'continuous':
         fig.line(dataset['x'][s], dataset['y'][s], color=colors[i], legend=name)
      elif dataset.attrs.get('datatype', None) == 'discrete':
         fig.square(dataset['x'][s], dataset['y'][s], color=colors[i], legend=name)
   
   fig.toolbar.logo=None
   fig.yaxis.axis_label = data.attrs['y']
   fig.xaxis.axis_label = data.attrs['x']
   fig.yaxis.axis_label_text_font_size = '10pt'
   fig.xaxis.axis_label_text_font_size = '10pt'
   fig.min_border = 5
   
   hdf.close()
   
   return fig

def plot_generic_large(datafile):
   """
   Generic plotting interface
   will plot the data and models as lines or circles/square. 
   """
   hdf = h5py.File(datafile, 'r') 
   data = hdf['DATA']
   models = hdf['MODEL']
   
   TOOLS = "pan, box_zoom, wheel_zoom, reset"
   
   fig = bpl.figure(plot_width=800, plot_height=600, toolbar_location='right',
                    tools=TOOLS)
   colors = ['red', 'blue', 'green']
   
   #-- plot the data
   bokehsource = bpl.ColumnDataSource()
   
   for i, (name, dataset) in enumerate(data.items()):
      
      if dataset.attrs.get('datatype', None) == 'continuous':
         fig.line(dataset['x'], dataset['y'], color=colors[i], line_dash='dashed', legend=name)
      elif dataset.attrs.get('datatype', None) == 'discrete':
         bokehsource.add(dataset['x'], name=name+'_x')
         bokehsource.add(dataset['y'], name=name+'_y')
         rend = fig.circle(name+'_x', name+'_y', color=colors[i], source=bokehsource,
                           size=7, legend=name)
         
         tooltips = [(data.attrs['x'], "@"+name+"_x")]
         if 'yerr' in dataset.dtype.names:
            bokehsource.add(dataset['yerr'], name=name+'_yerr')
            tooltips += [(data.attrs['y'], "@"+name+"_y +- @"+name+"_yerr")]
            
            plot_errorbars(fig, dataset['x'], dataset['y'], dataset['yerr'], 
                           line_width=2, color=colors[i])
         else:
            tooltips += [(data.attrs['y'], "@"+name+"_y")]
         
         hover_tool = mpl.HoverTool(renderers=[rend], tooltips=tooltips)
         fig.add_tools(hover_tool)
      
      
   
   #-- plot the models
   for i, (name, dataset) in enumerate(models.items()):
      
      if dataset.attrs.get('datatype', None) == 'continuous':
         fig.line(dataset['x'], dataset['y'], color=colors[i], legend=name)
      elif dataset.attrs.get('datatype', None) == 'discrete':
         fig.square(dataset['x'], dataset['y'], color=colors[i], legend=name)
   
   fig.toolbar.logo=None
   fig.yaxis.axis_label = data.attrs['y']
   fig.xaxis.axis_label = data.attrs['x']
   fig.yaxis.axis_label_text_font_size = '10pt'
   fig.xaxis.axis_label_text_font_size = '10pt'
   fig.min_border = 5
   
   hdf.close()
   
   #from bokeh.models import Button, CustomJS
   #button = Button(label='fullscreen')
   #button.callback = CustomJS(args=dict(fig=fig), code="""
      #var old_width = fig.width;
      #var doc = fig.document;
      #fig.width = old_width * 0.8;
      #doc.resize();
   #""")
   #http://stackoverflow.com/questions/39972162/dynamically-change-the-shape-of-bokeh-figure
   
   return fig#, button

def plot_generic_ci(datafile):
   
   hdf = h5py.File(datafile, 'r') 
   data = hdf['PARAMETERS']
   
   figures = {}
   
   for i, (name, dataset) in enumerate(data.items()):
      
      if 'Chi2Val' in dataset:
         
         err = dataset.attrs.get('err', 0.0)
         emin = dataset.attrs.get('emin', err)
         emax = dataset.attrs.get('emax', err)
         value = dataset.attrs.get('value', 0.0)
         
         title = "{} = {:.2f} + {:.2f} - {:.2f}".format(name, value, emax, emin)
         
         fig = bpl.figure(plot_width=280, plot_height=280, tools=[], responsive=False, title=title)
         
         fig.ray(x=dataset['Chi2Val']['x'], y=dataset['Chi2Val']['y'], length=0, 
               angle=np.pi/2., line_width=3)
         
         fig.line(dataset['Chi2Fit']['x'], dataset['Chi2Fit']['y'], line_width=1,
                  color='red', alpha=0.7)
         
         min_chi2 = np.min(dataset['Chi2Val']['y'])
         fig.y_range = mpl.Range1d(0.85*min_chi2, 1.25*min_chi2)
         
         fig.min_border = 10
         fig.min_border_top = 1
         fig.min_border_bottom = 40
         fig.toolbar.logo = None
         fig.toolbar_location = None
         fig.title.align = 'center'
      
         figures[name] = fig
      
   return figures



#============================================================================================
# SED fit plotting code
#============================================================================================

sed_colors = {'2MASS': 'black',
              'APASS' : 'blue',
             'STROMGREN': 'olive',
             'JOHNSON': 'gold',
             'GALEX': 'powderblue',
             'SDSS': 'aqua',
             'COUSINS': 'maroon',
             'DENIS': 'orange',
             'GENEVA': 'forestgreen ',}

def get_band_color(band):
   if band in sed_colors:
      return sed_colors[band]
   else:
      return 'black'

def plot_sedfit(datafile):
   """
   Plot an SED fit, including plotting the photometry, the synthetic photometry,
   and the best fitting model
   Small version for summary page. Not interactive.
   """
   
   flux_units='erg/s/cm2'
   
   data = fileio.read2dict(datafile)
   phot = data['master']
   sflux = data['results']['igrid_search']['synflux']
   model = data['results']['igrid_search']['model']
   
   wave = phot['cwave']
   flux,e_flux = conversions.convert('erg/s/cm2/AA', flux_units, phot['cmeas'], 
                                     phot['e_cmeas'], wave=(wave,'AA'))
   
   sel = np.where( ~np.isnan(flux) & phot['include'])
   wave, flux, e_flux = wave[sel], flux[sel], e_flux[sel]
   
   magorder = int( np.log10(np.max(flux)) ) - 1
   scale = 10**magorder
   flux, e_flux = flux / scale, e_flux / scale
   
   ymin = np.min(flux-e_flux) * 0.90 
   ymax = np.max(flux+e_flux) * 1.10
   xmin = np.min(wave) - 500
   xmax = np.max(wave) + 1000
   
   fig = bpl.figure(plot_width=600, plot_height=400, responsive=False, toolbar_location=None,
                    y_axis_type="log", y_range=(ymin, ymax),
                    x_axis_type="log", x_range=(xmin, xmax))
   
   #-- Plot the model
   x,y = model
   y = y / scale
   y = conversions.convert('erg/s/cm2/AA',flux_units,y,wave=(x,'AA'))
   fig.line(x, y, color='red', legend='binary model')
   
   #-- plot integrated photometry
   x, y = sflux['iwave'], sflux['iflux'] / scale
   y = conversions.convert('erg/s/cm2/AA',flux_units,y,wave=(x,'AA'))
   fig.x(x, y, color='black', fill_alpha=0.7, line_alpha=1.0, size=9, line_width=3, legend='synthetic')
   
   #-- plot the observations
   fig.circle(wave, flux, color='blue', 
                 fill_alpha=0.3, line_alpha=1.0, size=9, line_width=1.5, legend='observed')
   plot_errorbars(fig, wave, flux, e_flux, color='blue')
      
   fig.toolbar.logo=None
   fig.yaxis.axis_label = 'Flux_lambda * 10^{} (erg/s/cm2)'.format(-magorder)
   fig.xaxis.axis_label = 'Wavelength (AA)'
   fig.yaxis.axis_label_text_font_size = '10pt'
   fig.xaxis.axis_label_text_font_size = '10pt'
   fig.min_border = 5
   
   return fig

def plot_sedfit_large(datafile):
   """
   Plot an SED fit, including plotting the photometry in different colors depeding on 
   the photometric system, and the best fitting model
   Large version with hover function showing the observed points.
   """
   
   flux_units='erg/s/cm2'
   
   data = fileio.read2dict(datafile)
   phot = data['master']
   sflux = data['results']['igrid_search']['synflux']
   model = data['results']['igrid_search']['model']
   
   wave = phot['cwave']
   flux,e_flux = conversions.convert('erg/s/cm2/AA', flux_units, phot['cmeas'], 
                                     phot['e_cmeas'], wave=(wave,'AA'))
   fsystem = np.array([b.split('.')[0] for b in phot['photband']], dtype=str)
   
   sel = np.where( ~np.isnan(flux) & phot['include'])
   wave, flux, e_flux, fsystem = wave[sel], flux[sel], e_flux[sel], fsystem[sel]
   phot = phot[sel]
   
   #-- scale flux so that y axes is better readable
   magorder = int( np.log10(np.max(flux)) ) - 1
   scale = 10**magorder
   flux, e_flux = flux / scale, e_flux / scale
   
   
   #-- create data source for bokeh and hover information
   photd = dict(wave = wave,
                flux = flux,
                band = phot['photband'],
                mag = phot['meas'],
                e_mag = phot['e_meas'],
                unit = phot['unit'],
                source = phot['source'],)
   photsource = bpl.ColumnDataSource(data=photd)
   hover = mpl.HoverTool(tooltips=[("band", "@band"), ("measurement", "@mag +- @e_mag (@unit)"),
                                   ("source", "@source")], names=['hover'])
   
   
   tools = [mpl.PanTool(), mpl.WheelZoomTool(), 
            mpl.BoxZoomTool(), mpl.ResetTool(), hover]
   
   ymin = np.min(flux-e_flux) * 0.90 
   ymax = np.max(flux+e_flux) * 1.10
   xmin = np.min(wave) - 500
   xmax = np.max(wave) + 1000
   
   fig = bpl.figure(plot_width=800, plot_height=600, responsive=False, toolbar_location="right",
                    y_axis_type="log", y_range=(ymin, ymax),
                    x_axis_type="log", x_range=(xmin, xmax),
                    tools=tools)
   
   #-- Plot the model
   x,y = model
   y = y / scale
   y = conversions.convert('erg/s/cm2/AA',flux_units,y,wave=(x,'AA'))
   fig.line(x, y, color='red')
   
   #-- plot integrated photometry
   x, y = sflux['iwave'], sflux['iflux'] / scale
   y = conversions.convert('erg/s/cm2/AA',flux_units,y,wave=(x,'AA'))
   fig.x(x, y, color='black', fill_alpha=0.7, line_alpha=1.0, size=12, line_width=3)
   
   #-- plot the observations
   fig.circle('wave', 'flux', color='white', source=photsource, name='hover',
                 fill_alpha=0.0, line_alpha=0.0, size=14, line_width=2)
   
   for band in set(fsystem):
      sel = np.where(fsystem == band)
      fig.circle(wave[sel], flux[sel], color=get_band_color(band), 
                 fill_alpha=0.4, line_alpha=1.0, size=12, line_width=2, legend=band)
      
      plot_errorbars(fig, wave[sel], flux[sel], e_flux[sel], color=get_band_color(band),
                     line_width = 3.0)
      
   fig.toolbar.logo=None
   fig.yaxis.axis_label = 'Flux_lambda * 10^{} (erg/s/cm2)'.format(-magorder)
   fig.xaxis.axis_label = 'Wavelength (AA)'
   fig.yaxis.axis_label_text_font_size = '10pt'
   fig.xaxis.axis_label_text_font_size = '10pt'
   fig.min_border = 5
   
   return fig

def plot_sedfit_ci2d(datafile):
   """
   Plot the CI2D images for the SED fit
   """
   from matplotlib import _cntr as cntr
   
   figures = {}
   
   try:
      data = fileio.read2dict(datafile)
      ci2d = data['results']['igrid_search']['CI2D']
   except Exception:
      return figures
   
   for name, ci in ci2d.items():
      
      print name, ci.keys()
      
      x0, x1 = ci['x'][0], ci['x'][-1]
      y0, y1 = ci['y'][0], ci['y'][-1]
      data = ci['ci_red']
      x, y = np.mgrid[:data.shape[0], :data.shape[1]]
      
      c = cntr.Cntr(x, y, data)
      
      
      def scale(segments, rmin, rmax):
         smin = np.min(segments)
         ds = np.max(segments) - np.min(segments)
         dr = rmax - rmin
         return rmin + (segments - smin) / ds * dr
      
      
      
      fig = bpl.figure(plot_width=280, plot_height=280, 
                       title = name, tools=[], responsive=False)
      
      for i in np.linspace(0, 1, 10):
         res = c.trace(i)
         nseg = len(res) // 2
         segments, codes = res[:nseg], res[nseg:]
         
         if segments == []: continue
         
         xseg = scale(segments[0][:,0], x0, x1)
         yseg = scale(segments[0][:,1], y0, y1)
         
         fig.patch(xseg, yseg, line_width=2, fill_alpha=0.0)
                       
      
      fig.min_border = 10
      fig.min_border_top = 1
      fig.min_border_bottom = 40
      fig.toolbar.logo = None
      fig.toolbar_location = None
      fig.title.align = 'center'
      
      figures[name] = fig
      
   
   return figures


def plot_dataset(datafile, method):
   """
   General plotting function for analysis
   """
   
   if method.name == 'SED fit':
      return plot_sedfit(datafile)
   else:
      return plot_generic(datafile)
   
def plot_dataset_large(datafile, method):
   """
   General plotting function for analysis, makes the large version plot for 
   the detail pages including extra info when hovering over a figure
   """
   
   if method.name == 'SED fit':
      return plot_sedfit_large(datafile)
   else:
      return plot_generic_large(datafile)
   
def plot_parameter_ci(datafile, method):
   """
   General plotting function for the confidence intervals of the parameters. 
   This will return a figure for each confidence interval (1D) that is included
   in the datafile
   """
   
   if method.name == 'SED fit':
      return plot_sedfit_ci2d(datafile)
   else:
      return plot_generic_ci(datafile)