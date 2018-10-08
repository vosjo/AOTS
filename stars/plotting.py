 
"""
collection of all necessary bokeh plotting scripts
"""

import numpy as np

from .models import Star

from bokeh import plotting as bpl
from bokeh import models as mpl

#from analysis.aux.units import conversions as cv

wavelengths = {'GALEX.FUV': 1529 ,
               'GALEX.NUV': 2312 ,
               'JOHNSON.B': 4433 ,
               'JOHNSON.V': 5510 ,
               'SDSS.G':    4677 ,
               'SDSS.R':    6168 ,
               'SDSS.I':    7495 ,
               '2MASS.J':   12393,
               '2MASS.H':   16495,
               '2MASS.Ks':  21639,}

def plot_photometry(star_id):
   """
   Plot the photometry belonging to the given star ID
   """
   
   #-- obtain all photometry
   star = Star.objects.get(pk=star_id)
   photometry = []
   for p in star.photometry_set.all():
      if p.measurement <= 0:
         continue
      s, f = p.band.split('.')
      flux = cv.convert(p.unit, 'erg/s/cm2', p.measurement, photband=p.band)
      photometry.append((s, f, wavelengths[p.band], p.measurement, p.error, p.unit, flux))
   dtypes = [('system', 'a30'), ('filter', 'a10') , ('wave', 'f8'), ('meas', 'f8'), 
             ('emeas', 'f8'), ('unit', 'a50'), ('flux', 'f8')]
   photometry = np.array(photometry, dtype=dtypes)
   
   ymin = np.min(photometry['flux']) * 0.90 
   ymax = np.max(photometry['flux']) * 1.10
   
   tools = [mpl.PanTool(), mpl.WheelZoomTool(), 
            mpl.BoxZoomTool(), mpl.ResizeTool(), mpl.ResetTool()]
   
   fig = bpl.figure(plot_width=600, plot_height=400, responsive=False, toolbar_location="right",
                    y_axis_type="log", y_range=(ymin, ymax),
                    x_axis_type="log", x_range=(1200, 26000),
                    tools=tools)
   
   colors = {'GALEX': 'powderblue',
             'JOHNSON': 'gold',
             'SDSS': 'aqua',
             '2MASS': 'black',} 
   for band in colors.keys():
      sel = np.where(photometry['system'] == band)
      fig.circle(photometry[sel]['wave'], photometry[sel]['flux'], color=colors[band], 
                 fill_alpha=0.3, line_alpha=1.0, size=9, line_width=1.5, legend=band)
   
   fig.toolbar.logo=None
   fig.yaxis.axis_label = 'Flux_lambda (erg/s/cm2)'
   fig.xaxis.axis_label = 'Wavelength (AA)'
   fig.yaxis.axis_label_text_font_size = '10pt'
   fig.xaxis.axis_label_text_font_size = '10pt'
   fig.min_border = 5
   
   return fig
