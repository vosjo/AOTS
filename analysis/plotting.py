 
""" 
collection of all necessary bokeh plotting functions for analysis methods
"""
import h5py

import numpy as np

from bokeh import plotting as bpl
from bokeh import models as mpl
from bokeh.models import widgets 

def plot_errorbars(fig, x, y, e, **kwargs):
   """
   Plot errorbars on a bokeh plot
   """
   err_xs, err_ys = [], []
   for x, y, yerr in zip(x, y, e):
      err_xs.append((x, x))
      err_ys.append((y - yerr, y + yerr))
   fig.multi_line(err_xs, err_ys, **kwargs)

def plot_generic(hdf):
   """
   Generic plotting interface
   """
   
   fig = bpl.figure(plot_width=600, plot_height=400, responsive=False, toolbar_location=None)
   colors = ['red', 'blue']
   
   #-- plot the data
   data = hdf['DATA']
   for i, (name, dataset) in enumerate(data.items()):
      fig.circle(dataset['x'], dataset['y'], color=colors[i], legend=name)
      
      if 'yerr' in dataset.dtype.names:
         plot_errorbars(fig, dataset['x'], dataset['y'], dataset['yerr'], color=colors[i])
   
   #-- plot the models
   models = hdf['MODEL']
   for i, (name, dataset) in enumerate(models.items()):
      fig.line(dataset['x'], dataset['y'], color=colors[i], legend=name)
      
   
   fig.toolbar.logo=None
   fig.yaxis.axis_label = data.attrs['y']
   fig.xaxis.axis_label = data.attrs['x']
   fig.yaxis.axis_label_text_font_size = '10pt'
   fig.xaxis.axis_label_text_font_size = '10pt'
   fig.min_border = 5
   
   return fig

def plot_rvcurve(data):
   
   ms = data['MS']
   sdb = data['sdB']
   
   fig = bpl.figure(plot_width=600, plot_height=400, responsive=False, toolbar_location=None)
   
   fig.circle(ms['hjd'] - 2450000, ms['rv'], color='red', legend='MS')
   fig.square(sdb['hjd'] - 2450000, sdb['rv'], color='blue', legend='sdB')
   
   plot_errorbars(fig, ms['hjd'] - 2450000, ms['rv'], ms['err'], color='red')
   plot_errorbars(fig, sdb['hjd'] - 2450000, sdb['rv'], sdb['err'], color='blue')
   
   fig.toolbar.logo=None
   fig.yaxis.axis_label = 'Radial velocity (km/s)'
   fig.xaxis.axis_label = 'HJD - 2450000'
   fig.yaxis.axis_label_text_font_size = '10pt'
   fig.xaxis.axis_label_text_font_size = '10pt'
   fig.min_border = 5
   
   return fig

def plot_sedfit(data):
   
   #-- create data source for bokeh and hover information
   phot = data['photometry']
   photd = dict(wave = phot['wave'],
                flux = phot['flux'],
                band = phot['photband'],
                mag = ["{} +- {}".format(m,e) for m,e in zip(phot['mag'], phot['e_mag'])],
                source = phot['source'],)
   photsource = bpl.ColumnDataSource(data=photd)
   hover = mpl.HoverTool(tooltips=[("band", "@band"), ("magnitude", "@mag"), ("source", "@source")],
                         names=['hover'])
   
   #-- calculate the limits of the plot
   ymin = np.min(phot['flux']-phot['e_flux']) * 0.90 
   ymax = np.max(phot['flux']+phot['e_flux']) * 1.10
   xmin, xmax = 1200, 26000
   
   colors = {'2MASS': 'black',
             'STROMGREN': 'olive',
             'JOHNSON': 'gold',
             'GALEX': 'powderblue',
             'SDSS': 'aqua',
             'COUSINS': 'maroon',
             'DENIS': 'orange',}
   
   tools = [mpl.PanTool(), mpl.WheelZoomTool(), 
            mpl.BoxZoomTool(), mpl.ResizeTool(), mpl.ResetTool(), hover]
   
   fig = bpl.figure(plot_width=600, plot_height=400, responsive=False, toolbar_location="right",
                    y_axis_type="log", y_range=(ymin, ymax),
                    x_axis_type="log", x_range=(xmin, xmax),
                    tools=tools)
   
   #-- plot the model
   fig.line(data['wave'], data['flux'], color='red')
   
   #-- plot integrated photometry
   sphot = data['sphotometry']
   for band in set(sphot['system']):
      sel = np.where(sphot['system'] == band)
      fig.x(sphot['wave'][sel], sphot['flux'][sel], color=colors[band], 
                 fill_alpha=0.7, line_alpha=1.0, size=9, line_width=3)
   
   
   #-- plot observed photometry
   fig.circle('wave', 'flux', size=8, color='white', alpha=0.1, name='hover', source=photsource)
   
   for band in set(phot['system']):
      sel = np.where(phot['system'] == band)
      fig.circle(phot['wave'][sel], phot['flux'][sel], color=colors[band], 
                 fill_alpha=0.3, line_alpha=1.0, size=9, line_width=1.5, legend=band)
      
      plot_errorbars(fig, phot['wave'][sel], phot['flux'][sel], phot['e_flux'][sel],
                     color=colors[band])
   
   
   
   
   fig.toolbar.logo=None
   fig.yaxis.axis_label = 'Flux_lambda (erg/s/cm2)'
   fig.xaxis.axis_label = 'Wavelength (AA)'
   fig.yaxis.axis_label_text_font_size = '10pt'
   fig.xaxis.axis_label_text_font_size = '10pt'
   fig.min_border = 5
   
   return fig

def plot_analysis_method(datafile, analysis_type):
   """
   General plotting function for analysis
   """
   
   hdf = h5py.File(datafile, 'r') 
   return plot_generic(hdf)
   hdf.close()
   
   #if analysis_type == 'RV':
      #return plot_rvcurve(data)
   
   #else:
      
      #fig = bpl.figure(plot_width=300, plot_height=300, responsive=False, toolbar_location=None,
                     #y_range=(0, 100), x_range=(0,100))
      
      #fig.toolbar.logo=None
      #fig.yaxis.axis_label = 'RV (km/s)'
      #fig.xaxis.axis_label = 'HJD - 2450000'
      
      #return fig