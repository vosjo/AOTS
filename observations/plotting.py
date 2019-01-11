""" 
collection of all necessary bokeh plotting functions for spectra
"""
import re
import ephem
import numpy as np

import astropy.units as u
from astropy.time import Time
from astropy.coordinates import SkyCoord, AltAz, get_moon

from .models import Spectrum
from stars.models import Star

from bokeh import plotting as bpl
from bokeh import models as mpl
from bokeh.models import widgets, FuncTickFormatter

from observations.aux import tools as spectools

zeropoints = {
            'GALEX.FUV':  4.72496e-08, 
            'GALEX.NUV':  2.21466e-08, 
            'GAIA2.G':    2.46973e-09,
            'GAIA2.BP':   4.0145e-09,
            'GAIA2.RP':   1.28701e-09,
            'APASS.B':    6.40615e-09,
            'APASS.V':    3.66992e-09,
            'APASS.G':    4.92257e-09,
            'APASS.R':    2.85425e-09,
            'APASS.I':    1.94038e-09,
            '2MASS.J':    3.11048e-10,
            '2MASS.H':    1.13535e-10,
            '2MASS.K':    4.27871e-11,
            'WISE.W1':    8.1787e-12,
            'WISE.W2':    2.415e-12,
            'WISE.W3':    6.5151e-14,
            'WISE.W4':    5.0901e-15,
            }


def plot_visibility(spectrum_id):
   """
   Plot airmass and moondistance on the night of observations
   """
   
   fig = bpl.figure(plot_width=400, plot_height=240, toolbar_location=None,
                     y_range=(0, 90), x_axis_type="datetime")
   
   try:
   
      spectrum = Spectrum.objects.get(pk=spectrum_id)
      observatory = spectrum.observatory.get_EarthLocation()
      
      time = Time(spectrum.hjd, format='jd')
      
      sunset, sunrise = spectrum.observatory.get_sunset_sunrise(time)
      
      times = np.linspace(sunset.jd, sunrise.jd, 100)
      times = Time(times, format='jd')
      
      
      star = SkyCoord(ra=spectrum.ra*u.deg, dec=spectrum.dec*u.deg,)
      
      
      
      frame_star = AltAz(obstime=times, location=observatory) 

      star_altaz = star.transform_to(frame_star)  

      moon = get_moon(times)
      moon_altaz = moon.transform_to(frame_star) 
      
      
      times = times.to_datetime()
      
      
      fig.line(times, star_altaz.alt, color='blue', line_width=2)
      fig.line(times, moon_altaz.alt, color='orange', line_dash='dashed', line_width=2)
      
      
      obsstart = (time-spectrum.exptime/2*u.second).to_datetime()
      obsend = (time+spectrum.exptime/2*u.second).to_datetime()
      obs = mpl.BoxAnnotation(left=obsstart, right=obsend, fill_alpha=0.5, fill_color='red')
      fig.add_layout(obs)
   
   except:
      
      label = mpl.Label(x=75, y=40, x_units='screen', text='Could not calculate visibility', render_mode='css',
      border_line_color='red', border_line_alpha=1.0, text_color='red',
      background_fill_color='white', background_fill_alpha=1.0)
      
      fig.add_layout(label)
   
   fig.toolbar.logo=None
   fig.title.align = 'center'
   fig.yaxis.axis_label = 'Altitude (dgr)'
   fig.xaxis.axis_label = 'UT'
   fig.yaxis.axis_label_text_font_size = '10pt'
   fig.xaxis.axis_label_text_font_size = '10pt'
   fig.min_border = 5
   
   return fig

def plot_spectrum(spectrum_id, rebin=1):
   
   spectrum = Spectrum.objects.get(pk=spectrum_id)
   barycor = spectrum.barycor
   
   instrument = spectrum.instrument
   
   specfiles = spectrum.specfile_set.order_by('filetype')
   
   tabs = []
   for specfile in specfiles:
      wave, flux, header = specfile.get_spectrum()
      
      if instrument == 'UVES':
         wave = spectools.doppler_shift(wave, barycor)
         wave, flux = spectools.rebin_spectrum(wave, flux, binsize=rebin)
      elif instrument == 'HERMES' or instrument == 'FEROS':
         sel = np.where(wave > 3860)
         wave, flux = wave[sel], flux[sel]
         wave, flux = spectools.rebin_spectrum(wave, flux, binsize=rebin)
      else:
         wave, flux = spectools.rebin_spectrum(wave, flux, binsize=rebin)
      
      #-- set the maximum so that weird peaks are cut off automatically. 
      fsort = np.sort(flux)[::-1]
      maxf = fsort[int(np.floor(len(flux)/100.))] * 1.10
      
      fig = bpl.figure(plot_width=1600, plot_height=400, y_range=[np.min(flux) * 0.95, maxf]) #, sizing_mode='scale_width'
      fig.line(wave, flux, line_width=1, color="blue")
      
      #-- annotate He lines
      Helines = [(4388, 'red'), (4471, 'red'), (4541, 'blue'), (4684, 'blue'), (4922, 'red'), (5876, 'red'), (6678, 'red')]
      HeAnnot = []
      for h in Helines:
         if h[0] > wave[0] and h[0] < wave[-1]:
            HeAnnot.append(mpl.BoxAnnotation(plot=fig, left=h[0]-2, right=h[0]+2, fill_alpha=0.3, fill_color=h[1]))
      fig.renderers.extend(HeAnnot)
      
      fig.toolbar.logo=None
      fig.yaxis.axis_label = 'Flux'
      fig.xaxis.axis_label = 'Wavelength (AA)'
      fig.yaxis.axis_label_text_font_size = '10pt'
      fig.xaxis.axis_label_text_font_size = '10pt'
      fig.min_border = 5
      
      tabs.append(widgets.Panel(child=fig, title=specfile.filetype))
   
   tabs = widgets.Tabs(tabs=tabs)
   return tabs

def plot_sed(star_id):
   
   star = Star.objects.get(pk=star_id)
   
   photometry = star.photometry_set.all()
   
   
   meas, flux, err, wave, bands, system = [], [], [], [], [], []
   for point in photometry:
      
      if not point.band in zeropoints: continue
      zp = zeropoints[point.band]
      bands.append(point.band)
      system.append(point.band.split('.')[0])
      meas.append(point.measurement)
      flux.append(zp * 10**(-point.measurement / 2.5))
      err.append(point.error)
      wave.append(point.wavelength)
   
   meas, flux, err, wave, bands, system = np.array(meas), np.array(flux), np.array(err), np.array(wave), np.array(bands), np.array(system), 
   
   photd = dict(wave = wave,
                flux = flux,
                band = bands,
                mag = meas,
                err = err,)
   photsource = bpl.ColumnDataSource(data=photd)
   hover = mpl.HoverTool(tooltips=[("band", "@band"), ("magnitude", "@mag +- @err")],
                         names=['hover'])
      
   tools = [mpl.PanTool(), mpl.WheelZoomTool(), 
            mpl.BoxZoomTool(), mpl.ResetTool(), hover]
   fig = bpl.figure(plot_width=600, plot_height=400, x_axis_type="log", y_axis_type="log", tools=tools)
   
   #fig.circle(wave, meas)
   fig.circle('wave', 'flux', size=8, color='white', alpha=0.1, name='hover', source=photsource)
   
   colors = {'2MASS': 'black',
             'WISE': 'gray',
             'STROMGREN': 'olive',
             'GAIA2': 'maroon',
             'APASS': 'gold',
             'GALEX': 'powderblue',
              } 
   
   for band in set(system):
      sel = np.where(system == band)
      fig.circle(wave[sel], flux[sel], color=colors[band], 
                 fill_alpha=0.3, line_alpha=1.0, size=9, line_width=1.5)
   
   fig.toolbar.logo=None
   fig.yaxis.axis_label = 'Flux'
   fig.xaxis.axis_label = 'Wavelength (AA)'
   fig.yaxis.axis_label_text_font_size = '10pt'
   fig.xaxis.axis_label_text_font_size = '10pt'
   fig.min_border = 5
   
   return fig
