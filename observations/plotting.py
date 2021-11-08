"""
collection of all necessary bokeh plotting functions for spectra
"""
import re
import ephem
import numpy as np

import astropy.units as u
from astropy.time import Time
from astropy.coordinates import SkyCoord, AltAz, get_moon

from specutils import Spectrum1D

from .models import Spectrum, LightCurve
from stars.models import Star

from bokeh import plotting as bpl
from bokeh import models as mpl
from bokeh.models import widgets, FuncTickFormatter

from observations.auxil import tools as spectools


zeropoints = {
            'GALEX.FUV':  4.72496e-08,
            'GALEX.NUV':  2.21466e-08,
            'GAIA2.G':    2.46973e-09,
            'GAIA2.BP':   4.0145e-09,
            'GAIA2.RP':   1.28701e-09,
            'SKYMAP.U':   8.93655e-09,
            'SKYMAP.V':   7.38173e-09,
            'SKYMAP.G':   4.18485e-09,
            'SKYMAP.R':   2.85924e-09,
            'SKYMAP.I':   1.79368e-09,
            'SKYMAP.Z':   1.29727e-09,
            'APASS.B':    6.40615e-09,
            'APASS.V':    3.66992e-09,
            'APASS.G':    4.92257e-09,
            'APASS.R':    2.85425e-09,
            'APASS.I':    1.94038e-09,
            'SDSS.U':     3.493e-9,
            'SDSS.G':     5.352e-9,
            'SDSS.R':     2.541e-9,
            'SDSS.I':     1.323e-9,
            'SDSS.Z':     7.097e-10,
            'PANSTAR.G':  4.704969e-09,
            'PANSTAR.R':  2.859411e-09,
            'PANSTAR.I':  1.924913e-09,
            'PANSTAR.Z':  1.451480e-09,
            'PANSTAR.Y':  1.176242e-09,
            '2MASS.J':    3.11048e-10,
            '2MASS.H':    1.13535e-10,
            '2MASS.K':    4.27871e-11,
            'WISE.W1':    8.1787e-12,
            'WISE.W2':    2.415e-12,
            'WISE.W3':    6.5151e-14,
            'WISE.W4':    5.0901e-15,
            }



def plot_visibility(observation):
   """
   Plot airmass and moondistance on the night of observations
   """

   fig = bpl.figure(plot_width=400, plot_height=240, toolbar_location=None,
                     y_range=(0, 90), x_axis_type="datetime")

   fig.toolbar.logo=None
   fig.title.align = 'center'
   fig.yaxis.axis_label = 'Altitude (dgr)'
   fig.xaxis.axis_label = 'UT'
   fig.yaxis.axis_label_text_font_size = '10pt'
   fig.xaxis.axis_label_text_font_size = '10pt'
   fig.min_border = 5

   try:

      if observation.observatory.space_craft:
         label = mpl.Label(x=180, y=110, x_units='screen', y_units='screen', text='Observatory is a Space Craft', render_mode='css',
         border_line_color='red', border_line_alpha=1.0, text_color='red', text_align='center', text_baseline='middle',
         background_fill_color='white', background_fill_alpha=1.0)

         fig.add_layout(label)

         return fig


      observatory = observation.observatory.get_EarthLocation()

      time = Time(observation.hjd, format='jd')

      sunset, sunrise = observation.observatory.get_sunset_sunrise(time)

      times = np.linspace(sunset.jd, sunrise.jd, 100)
      times = Time(times, format='jd')


      star = SkyCoord(ra=observation.ra*u.deg, dec=observation.dec*u.deg,)



      frame_star = AltAz(obstime=times, location=observatory)

      star_altaz = star.transform_to(frame_star)

      moon = get_moon(times)
      moon_altaz = moon.transform_to(frame_star)


      times = times.to_datetime()


      fig.line(times, star_altaz.alt, color='blue', line_width=2)
      fig.line(times, moon_altaz.alt, color='orange', line_dash='dashed', line_width=2)


      obsstart = (time-observation.exptime/2*u.second).to_datetime()
      obsend = (time+observation.exptime/2*u.second).to_datetime()
      obs = mpl.BoxAnnotation(left=obsstart, right=obsend, fill_alpha=0.5, fill_color='red')
      fig.add_layout(obs)

   except Exception as e:

      print (e)

      label = mpl.Label(x=75, y=40, x_units='screen', text='Could not calculate visibility', render_mode='css',
      border_line_color='red', border_line_alpha=1.0, text_color='red',
      background_fill_color='white', background_fill_alpha=1.0)

      fig.add_layout(label)

   return fig


def plot_spectrum(spectrum_id, rebin=1, normalize=True, porder=3):
    '''
    Plot spectrum

    Parameters:
    -----------
    spectrum_id
        ID of the spectrum
    rebin               int()
        Bin size
    normalize           bool()
        Normalize spectrum yes/no

    Returns:
    --------
    tabs

    '''

    #   Load spectrum, individual spectra (specfiles), and instrument
    spectrum   = Spectrum.objects.get(pk=spectrum_id)
    specfiles  = spectrum.specfile_set.order_by('filetype')
    instrument = spectrum.instrument

    #   Determine flux unit
    funit_str = spectrum.flux_units

    #   Set flux unit
    if funit_str == 'ADU':
        funit = u.adu
    elif funit_str == 'ergs/cm/cm/s/A':
        funit = u.erg/u.cm/u.cm/u.s/u.AA
    else:
        funit = u.ct

    #   Prepare list for tabs in the figure
    tabs = []

    #   Loop over spectra
    for specfile in specfiles:
        #   Extract data
        wave, flux, header = specfile.get_spectrum()

        #   Instrument specific settings
        if instrument == 'UVES':
            #   Set value for barycenter correction
            barycor = spectrum.barycor
            #   Apply barycenter correction
            wave = spectools.doppler_shift(wave, barycor)
        elif instrument == 'HERMES' or instrument == 'FEROS':
            #   Restrict wavelength range
            sel = np.where(wave > 3860)
            wave, flux = wave[sel], flux[sel]

        #   Rebin spectrum
        wave, flux = spectools.rebin_spectrum(wave, flux, binsize=rebin)


        ###
        #   Normalize & merge spectra

        #   Identify echelle spectra
        #   -> wave is a np.ndarray of np.ndarrays
        if isinstance(wave[0], np.ndarray):
            #   Set normalize to true if current value is 'None'
            if normalize == None:
                normalize = True

            #   Normalize & merge spectra
            if normalize:
                #   Prepare list for echelle orders
                orders = []

                #   Loop over each order
                for i,w in enumerate(wave):
                    #   Create Spectrum1D objects
                    orders.append(
                        Spectrum1D(
                            spectral_axis=w*u.AA,
                            flux=flux[i]*funit,
                            )
                        )

                #   Normalize & merge spectra
                wave, flux = spectools.norm_merge_spectra(orders, order=porder)
                wave       = wave.value

                #   Set flux unit to 'normalized'
                funit_str = 'normalized'
            else:
                #   Merge spectra
                wave, flux = spectools.merge_spectra(wave, flux)
        else:
            #   Normalize & merge spectra
            if normalize:
                #   Create Spectrum1D objects
                spec = Spectrum1D(spectral_axis=wave*u.AA, flux=flux*funit)

                #   Normalize spectrum
                spec, std = spectools.norm_spectrum(spec, order=porder)

                #   Split spectrum in 10 segments,
                #   if standard deviation is too high
                #   (might neglect some points at the red end)
                print('std', std)
                if std > 0.05:
                    nsegment = 5
                    nsegment = 10
                    nwave    = len(wave)
                    step     = int(nwave/nsegment)
                    segments = []

                    #   Loop over segments
                    i_old = 0
                    for i in range(step,step*nsegment,step):
                        #   Cut segments and add overlay range to the
                        #   segments, so that the normalization afterburner
                        #   can take effect
                        overlap = int(step*0.15)
                        if i == step:
                            flux_seg = flux[i_old:i+overlap]
                            wave_seg = wave[i_old:i+overlap]
                        elif i == nsegment-1:
                            flux_seg = flux[i_old-overlap:i]
                            wave_seg = wave[i_old-overlap:i]
                        else:
                            flux_seg = flux[i_old-overlap:i+overlap]
                            wave_seg = wave[i_old-overlap:i+overlap]
                        i_old = i


                        #   Create Spectrum1D objects for the segments
                        segments.append(
                            Spectrum1D(
                                spectral_axis=wave_seg*u.AA,
                                flux=flux_seg*funit,
                                )
                            )
                    #   Normalize & merge spectra
                    wave, flux = spectools.norm_merge_spectra(
                        segments,
                        order=porder,
                        )
                    wave       = wave.value

                else:
                    wave = np.asarray(spec.spectral_axis)
                    flux = np.asarray(spec.flux)

                #   Set flux unit to 'normalized'
                funit_str = 'normalized'

        #   Set the maximum and minimum so that weird peaks
        #   are cut off automatically.
        fsort = np.sort(flux)[::-1]
        maxf  = fsort[int(np.floor(len(flux)/100.))] * 1.2
        minf  = np.max([np.min(flux)*0.95, 0])

        #   Initialize figure
        #, sizing_mode='scale_width'
        fig = bpl.figure(plot_width=1550, plot_height=400, y_range=[minf, maxf])

        #   Plot spectrum
        fig.line(wave, flux, line_width=1, color="blue")

        #   Annotate He and H lines
        #   Define lines:
        Lines = [
            (3204.11, 'darkblue', 'HeII'),
            (3835.39, 'red', 'Hη'),
            (3888.05, 'red', 'Hζ'),
            (3970.07, 'red', 'Hε'),
            (4103., 'red', 'Hδ'),
            (4201., 'darkblue', 'HeII'),
            (4340.49, 'red', 'Hγ'),
            #(4339, 'darkblue', 'HeII'),
            (4471, 'blue', 'HeI'),
            (4542, 'darkblue', 'HeII'),
            (4687, 'darkblue', 'HeII'),
            (4861.36, 'red', 'Hβ'),
            (4922, 'blue', 'HeI'),
            (5412., 'darkblue', 'HeII'),
            (5877, 'blue', 'HeI'),
            (6562.1, 'red', 'Hα'),
            (6685, 'darkblue', 'HeII'),
            ]
        Annot = []

        #   For each line make an annotation box and and a label
        for h in Lines:
            #   Restrict to lines in plot range
            if h[0] > wave[0] and h[0] < wave[-1]:
                #   Make annotation
                Annot.append(
                    mpl.BoxAnnotation(
                        left=h[0]-2,
                        right=h[0]+2,
                        fill_alpha=0.3,
                        fill_color=h[1]
                        )
                    )
                #   Make label
                lab = mpl.Label(
                    x=h[0],
                    y=345.,
                    y_units='screen',
                    text=h[2],
                    angle=90,
                    angle_units='deg',
                    text_align='right',
                    text_color=h[1],
                    text_alpha=0.6,
                    text_font_size='14px',
                    border_line_color='white',
                    border_line_alpha=1.0,
                    background_fill_color='white',
                    background_fill_alpha=0.3,
                    )
                fig.add_layout(lab)
        #   Render annotations
        fig.renderers.extend(Annot)

        #   Set figure labels
        fig.toolbar.logo=None
        fig.yaxis.axis_label = 'Flux ('+funit_str+')'
        fig.xaxis.axis_label = 'Wavelength (AA)'
        fig.yaxis.axis_label_text_font_size = '10pt'
        fig.xaxis.axis_label_text_font_size = '10pt'
        fig.min_border = 5

        #   Fill tabs list
        tabs.append(widgets.Panel(child=fig, title=specfile.filetype))

    #   Make figure from tabs list
    tabs = widgets.Tabs(tabs=tabs)
    return tabs


def plot_lightcurve(lightcurve_id, period=None, binsize=0.01):

   lightcurve = LightCurve.objects.get(pk=lightcurve_id)

   time, flux, header = lightcurve.get_lightcurve()

   fig1 = bpl.figure(plot_width=1600, plot_height=400) #, sizing_mode='scale_width'
   fig1.line(time, flux, line_width=1, color="blue")

   fig1.toolbar.logo=None
   fig1.yaxis.axis_label = 'Flux'
   fig1.xaxis.axis_label = 'Time (TJD)'
   fig1.yaxis.axis_label_text_font_size = '10pt'
   fig1.xaxis.axis_label_text_font_size = '10pt'
   fig1.min_border = 5


   fig2 = bpl.figure(plot_width=1600, plot_height=400) #, sizing_mode='scale_width'

   if not period is None:
      # calculate phase and sort on phase
      phase = time % period / period
      inds = phase.argsort()
      phase, flux = phase[inds], flux[inds]

      # rebin the phase light curve
      phase, flux = spectools.rebin_phased_lightcurve(phase, flux, binsize=binsize)

      phase = np.hstack([phase,phase+1])
      flux = np.hstack([flux, flux])

      fig2.line(phase, flux, line_width=1, color="blue")

   else:

      label = mpl.Label(x=800, y=200, x_units='screen', y_units='screen',
                        text='No period provided, cannot phase fold lightcurve', render_mode='css', text_align='center',
                        border_line_color='red', border_line_alpha=1.0, text_color='red',
                        background_fill_color='white', background_fill_alpha=1.0)

      fig2.add_layout(label)

   fig2.toolbar.logo=None
   fig2.yaxis.axis_label = 'Flux'
   fig2.xaxis.axis_label = 'Phase'
   fig2.yaxis.axis_label_text_font_size = '10pt'
   fig2.xaxis.axis_label_text_font_size = '10pt'
   fig2.min_border = 5


   return fig1, fig2

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
             'SDSS':    'olive',
             'GAIA2': 'maroon',
             'APASS': 'gold',
             'GALEX': 'powderblue',
             'PANSTAR': 'green',
             'SKYMAP': 'red',
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
