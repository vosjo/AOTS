""" 
collection of all necessary bokeh plotting functions for spectra
"""
import re
import ephem
import numpy as np

import astropy.units as u
from astropy.time import Time
from astropy.coordinates import SkyCoord, EarthLocation, AltAz

from astropy.coordinates import get_moon

from astroplan import Observer

from .models import Spectrum

from .aux import observatories

from bokeh import plotting as bpl
from bokeh import models as mpl
from bokeh.models import widgets, FuncTickFormatter

from spectra.aux import tools as spectools

def plot_visibility_old(spectrum_id):
   """
   Plot airmass and moondistance on the night of observations
   """
   
   spectrum = Spectrum.objects.get(pk=spectrum_id)
   
   #-- define the observatory
   observatory = observatories.get_observatory(spectrum.telescope)
   moon, sun = ephem.Moon(), ephem.Sun()
   
   print( observatory)
   
   #-- get beginning and end of night and observation
   observatory.date = Time(spectrum.hjd, format='jd').iso
   print (observatory.date.__str__())
   night_start = observatory.previous_setting(sun)
   night_end = observatory.next_rising(sun)
   night_duration = (night_end - night_start) * 24 * 60 # in minutes
   
   print (night_start, night_end, night_duration / 24 / 60.)
   
   obs_start = observatory.date - spectrum.exptime / 2 * ephem.second
   obs_end = observatory.date + spectrum.exptime / 2 * ephem.second
   
   #-- define the star
   star = ephem.FixedBody()
   star._ra = ephem.degrees(spectrum.ra/180.*np.pi)
   star._dec = ephem.degrees(spectrum.dec/180*np.pi)
   
   #-- moon and weather information
   star.compute(observatory)
   moon.compute(observatory)

   
   #-- compute altitude
   date = []   
   observatory.date = night_start
   staralt, moonalt = [], []
   for i in range(25):
      date.append(observatory.date)
      star.compute(observatory)
      moon.compute(observatory)
      
      staralt.append(float(star.alt)/np.pi*180)
      moonalt.append(float(moon.alt)/np.pi*180)
      
      observatory.date += ephem.minute * night_duration / 20.
   
   fig = bpl.figure(plot_width=400, plot_height=240, toolbar_location=None,
                    y_range=(0, 90))
   
   print (date)
   print (staralt)
   
   fig.line(date, staralt, color='blue')
   fig.line(date, moonalt, color='orange', line_width=2)
   
   obs = mpl.BoxAnnotation(left=obs_start, right=obs_end, fill_alpha=0.5, fill_color='red')
   fig.add_layout(obs)
   
   ## convert gregorian time to UT hours
   #fig.xaxis.formatter = FuncTickFormatter(code="""
    #function (tick) {
        #var hour = (tick - Math.floor(tick)) / (1./24.);
        #var minute = hour - Math.floor(hour);
        #hour = (Math.floor(hour) + 12) % 24;
        #minute = Math.floor(minute / (1./60.));
        #return hour + ':' + minute;
    #};
   #""")
   
   fig.toolbar.logo=None
   #fig.title.text = 'Target Visibility'
   fig.title.align = 'center'
   fig.yaxis.axis_label = 'Altitude (dgr)'
   fig.xaxis.axis_label = 'UT'
   fig.yaxis.axis_label_text_font_size = '10pt'
   fig.xaxis.axis_label_text_font_size = '10pt'
   fig.min_border = 5
   
   return fig


def plot_visibility(spectrum_id):
   """
   Plot airmass and moondistance on the night of observations
   """
   
   spectrum = Spectrum.objects.get(pk=spectrum_id)
   
   observatory = EarthLocation(lat=28.7619*u.deg, lon=-17.8775*u.deg, height=2333*u.m)
   observer = Observer(name='Mercator',
               location=observatory,)
   
   time = Time(spectrum.hjd, format='jd')
   
   sunset = observer.sun_set_time(time, which='nearest')
   sunrise = observer.sun_rise_time(time, which='nearest')
   
   
   times = np.linspace(sunset.jd, sunrise.jd, 100)
   times = Time(times, format='jd')
   
   
   star = SkyCoord(ra=spectrum.ra*u.deg, dec=spectrum.dec*u.deg,)
   
   
   
   frame_star = AltAz(obstime=times, location=observatory) 

   star_altaz = star.transform_to(frame_star)  

   moon = get_moon(times)
   moon_altaz = moon.transform_to(frame_star) 
   
   
   times = times.to_datetime()
   
   fig = bpl.figure(plot_width=400, plot_height=240, toolbar_location=None,
                    y_range=(0, 90), x_axis_type="datetime")
   
   
   fig.line(times, star_altaz.alt, color='blue', line_width=2)
   fig.line(times, moon_altaz.alt, color='orange', line_dash='dashed', line_width=2)
   
   
   obsstart = (time-spectrum.exptime/2*u.second).to_datetime()
   obsend = (time+spectrum.exptime/2*u.second).to_datetime()
   obs = mpl.BoxAnnotation(left=obsstart, right=obsend, fill_alpha=0.5, fill_color='red')
   fig.add_layout(obs)
   
   
   fig.toolbar.logo=None
   #fig.title.text = 'Target Visibility'
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
   
