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

from bokeh import plotting as bpl
from bokeh import models as mpl
from bokeh.models import widgets, FuncTickFormatter

from spectra.aux import tools as spectools


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
      
      #if rebin > 1:
         #wave, flux = spectools.rebin_spectrum(wave, flux, binsize=rebin)
      
      if instrument == 'UVES':
         wave = spectools.doppler_shift(wave, barycor)
         wave, flux = spectools.rebin_spectrum(wave, flux, binsize=rebin)
      elif instrument == 'HERMES':
         sel = np.where(wave > 3860)
         wave, flux = wave[sel], flux[sel]
         wave, flux = spectools.rebin_spectrum(wave, flux, binsize=rebin)
      else:
         wave, flux = spectools.rebin_spectrum(wave, flux, binsize=rebin)
      
      fig = bpl.figure(plot_width=1600, plot_height=400) #, sizing_mode='scale_width'
      fig.line(wave, flux, line_width=1, color="blue")
      
      fig.toolbar.logo=None
      fig.yaxis.axis_label = 'Flux'
      fig.xaxis.axis_label = 'Wavelength (AA)'
      fig.yaxis.axis_label_text_font_size = '10pt'
      fig.xaxis.axis_label_text_font_size = '10pt'
      fig.min_border = 5
      
      tabs.append(widgets.Panel(child=fig, title=specfile.filetype))
   
   tabs = widgets.Tabs(tabs=tabs)
   return tabs
   
