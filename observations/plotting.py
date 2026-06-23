"""
collection of all necessary bokeh plotting functions for spectra
"""
import astropy.units as u
import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord, AltAz, get_body
from astropy.time import Time
from bokeh import models as mpl
from bokeh import plotting as bpl
from bokeh.models import TabPanel, Tabs
from specutils import Spectrum as SpecutilsSpectrum

from observations.auxil import tools as spectools
from dash.bokeh_theme import (
    apply_bokeh_figure_theme,
    apply_bokeh_tabs_theme,
    resolve_bokeh_theme,
    themed_field_hover_tool,
    themed_status_label,
)
from stars.models import Star
from stars.photometry_bands import SURVEY_PLOT_COLORS, ZEROPOINTS as zeropoints
from .models import Spectrum, LightCurve


def plot_visibility(observation, *, theme=None):
    """
    Plot airmass and moondistance on the night of observations
    """
    plot_theme = resolve_bokeh_theme(theme)

    fig = bpl.figure(
        height=200,
        sizing_mode='stretch_both',
        toolbar_location=None,
        y_range=(0, 90),
        x_axis_type="datetime",
    )

    fig.toolbar.logo = None
    fig.title.align = 'center'
    fig.yaxis.axis_label = 'Altitude (dgr)'
    fig.xaxis.axis_label = 'UT'
    fig.yaxis.axis_label_text_font_size = '10pt'
    fig.xaxis.axis_label_text_font_size = '10pt'
    fig.min_border = 5

    try:

        if observation.observatory.space_craft:
            label = themed_status_label(
                x=180,
                y=110,
                x_units='screen',
                y_units='screen',
                text='Observatory is a Space Craft',
                theme=plot_theme,
            )

            fig.add_layout(label)

            apply_bokeh_figure_theme(fig, plot_theme)
            return fig

        observatory = observation.observatory.get_EarthLocation()

        time = Time(observation.hjd, format='jd')

        sunset, sunrise = observation.observatory.get_sunset_sunrise(time)

        times = np.linspace(sunset.jd, sunrise.jd, 100)
        times = Time(times, format='jd')

        star = SkyCoord(ra=observation.ra * u.deg, dec=observation.dec * u.deg, )

        frame_star = AltAz(obstime=times, location=observatory)

        star_altaz = star.transform_to(frame_star)

        moon = get_body('moon', times)
        moon_altaz = moon.transform_to(frame_star)

        times = times.to_datetime()

        fig.line(times, star_altaz.alt, color=plot_theme.marker_fill, line_width=2)
        fig.line(times, moon_altaz.alt, color='orange', line_dash='dashed', line_width=2)

        obsstart = (time - observation.exptime / 2 * u.second).to_datetime()
        obsend = (time + observation.exptime / 2 * u.second).to_datetime()
        obs = mpl.BoxAnnotation(left=obsstart, right=obsend, fill_alpha=0.5, fill_color='red')
        fig.add_layout(obs)

    except Exception as e:

        print(e)

        label = themed_status_label(
            x=75,
            y=40,
            x_units='screen',
            text='Could not calculate visibility',
            theme=plot_theme,
        )

        fig.add_layout(label)

    apply_bokeh_figure_theme(fig, plot_theme)
    return fig


def plot_spectrum(spectrum_id, rebin=1, normalize=True, porder=3, project=None, *, theme=None):
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

    plot_theme = resolve_bokeh_theme(theme)

    #   Load spectrum, individual spectra (specfiles), and instrument
    spectrum = Spectrum.objects.select_related('project').get(pk=spectrum_id)
    from AOTS.project_scoping import assert_plot_belongs_to_project
    assert_plot_belongs_to_project(spectrum, project)
    specfiles = spectrum.specfile_set.order_by('filetype')
    instrument = spectrum.instrument

    #   Determine flux unit
    funit_str = spectrum.flux_units

    #   Set flux unit
    if funit_str == 'ADU':
        funit = u.adu
    elif funit_str == 'ergs/cm/cm/s/A':
        funit = u.erg / u.cm / u.cm / u.s / u.AA
    else:
        funit = u.ct

    #   Prepare list for tabs in the figure
    tabs = []

    #   Loop over spectra
    for specfile in specfiles:
        #   Extract data
        wave, flux, header = specfile.get_spectrum()

        #   Barycentric correction
        if not spectrum.barycor_bool:
            #   Set value for barycenter correction
            barycor = spectrum.barycor
            #   Apply barycenter correction
            wave = spectools.doppler_shift(wave, barycor)

        #   Instrument specific settings
        if instrument == 'HERMES' or instrument == 'FEROS':
            #   Restrict wavelength range
            sel = np.where(wave > 3860)
            wave, flux = wave[sel], flux[sel]

        #   Rebin spectrum
        #   If the spectrum is already normalized, set 'mean' to True to keep
        #   the continuum at ~1.
        if spectrum.normalized:
            wave, flux = spectools.rebin_spectrum(
                wave,
                flux,
                binsize=rebin,
                mean=True,
            )
        else:
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
                for i, w in enumerate(wave):
                    #   Create Spectrum objects
                    orders.append(
                        SpecutilsSpectrum(
                            spectral_axis=w * u.AA,
                            flux=flux[i] * funit,
                        )
                    )

                #   Normalize & merge spectra
                wave, flux = spectools.norm_merge_spectra(orders, order=porder)
                wave = wave.value

                #   Set flux unit to 'normalized'
                funit_str = 'normalized'
            else:
                #   Merge spectra
                wave, flux = spectools.merge_spectra(wave, flux)
        else:
            #   Normalize & merge spectra
            if normalize:
                #   Create Spectrum object
                spec = SpecutilsSpectrum(spectral_axis=wave * u.AA, flux=flux * funit)

                #   Normalize spectrum
                spec, std = spectools.norm_spectrum(spec, order=porder)

                #   Split spectrum in 10 segments,
                #   if standard deviation is too high
                if std > 0.05:
                    nsegment = 10
                    nwave = len(wave)
                    step = int(nwave / nsegment)
                    segments = []

                    #   Loop over segments
                    i_old = 0
                    for i in range(step, step * nsegment, step):
                        #   Cut segments and add overlay range to the
                        #   segments, so that the normalization afterburner
                        #   can take effect
                        overlap = int(step * 0.15)
                        if i == step:
                            flux_seg = flux[i_old:i + overlap]
                            wave_seg = wave[i_old:i + overlap]
                        elif i == nsegment - 1:
                            flux_seg = flux[i_old - overlap:]
                            wave_seg = wave[i_old - overlap:]
                        else:
                            flux_seg = flux[i_old - overlap:i + overlap]
                            wave_seg = wave[i_old - overlap:i + overlap]
                        i_old = i

                        #   Create Spectrum objects for the segments
                        segments.append(
                            SpecutilsSpectrum(
                                spectral_axis=wave_seg * u.AA,
                                flux=flux_seg * funit,
                            )
                        )
                    #   Normalize & merge spectra
                    wave, flux = spectools.norm_merge_spectra(
                        segments,
                        order=porder,
                    )
                    wave = wave.value

                else:
                    wave = np.asarray(spec.spectral_axis)
                    flux = np.asarray(spec.flux)

                #   Set flux unit to 'normalized'
                funit_str = 'normalized'

        #   Set the maximum and minimum so that weird peaks
        #   are cut off automatically.
        fsort = np.sort(flux)[::-1]
        maxf = fsort[int(np.floor(len(flux) / 100.))] * 1.2
        minf = np.max([np.min(flux) * 0.95, 0])

        #   Initialize figure
        fig = bpl.figure(
            height=250,
            sizing_mode='scale_width',
            y_range=[minf, maxf],
        )

        #   Plot spectrum
        fig.line(wave, flux, line_width=1, color=plot_theme.marker_fill)

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
            # (4339, 'darkblue', 'HeII'),
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
                        left=h[0] - 2,
                        right=h[0] + 2,
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
                    border_line_color=plot_theme.outline,
                    border_line_alpha=1.0,
                    background_fill_color=plot_theme.plot_border,
                    background_fill_alpha=0.3,
                )
                fig.add_layout(lab)
        #   Render annotations
        fig.renderers.extend(Annot)

        #   Set figure labels
        fig.toolbar.logo = None
        fig.yaxis.axis_label = 'Flux (' + funit_str + ')'
        fig.xaxis.axis_label = 'Wavelength (AA)'
        fig.yaxis.axis_label_text_font_size = '10pt'
        fig.xaxis.axis_label_text_font_size = '10pt'
        fig.min_border = 5

        apply_bokeh_figure_theme(fig, plot_theme)

        #   Fill tabs list
        tabs.append(TabPanel(child=fig, title=specfile.filetype))

    #   Make figure from tabs list
    tabs_widget = Tabs(tabs=tabs, sizing_mode='scale_width')
    apply_bokeh_tabs_theme(
        tabs_widget,
        plot_theme,
        mode='light' if theme == 'light' else 'dark',
    )
    return tabs_widget


def plot_lightcurve(lightcurve_id, period=None, binsize=0.01, project=None, *, theme=None):
    plot_theme = resolve_bokeh_theme(theme)
    lightcurve = LightCurve.objects.select_related('project').get(pk=lightcurve_id)
    from AOTS.project_scoping import assert_plot_belongs_to_project
    assert_plot_belongs_to_project(lightcurve, project)

    time, flux, header = lightcurve.get_lightcurve()

    fig1 = bpl.figure(width=1600, height=400, sizing_mode='scale_width')
    fig1.line(time, flux, line_width=1, color=plot_theme.marker_fill)

    fig1.toolbar.logo = None
    fig1.yaxis.axis_label = 'Flux'
    fig1.xaxis.axis_label = 'Time (TJD)'
    fig1.yaxis.axis_label_text_font_size = '10pt'
    fig1.xaxis.axis_label_text_font_size = '10pt'
    fig1.min_border = 5

    fig2 = bpl.figure(width=1600, height=400, sizing_mode='scale_width')

    if not period is None:
        # calculate phase and sort on phase
        phase = time % period / period
        inds = phase.argsort()
        phase, flux = phase[inds], flux[inds]

        # rebin the phase light curve
        phase, flux = spectools.rebin_phased_lightcurve(phase, flux, binsize=binsize)

        phase = np.hstack([phase, phase + 1])
        flux = np.hstack([flux, flux])

        fig2.line(phase, flux, line_width=1, color=plot_theme.marker_fill)

    else:

        label = themed_status_label(
            x=800,
            y=200,
            x_units='screen',
            y_units='screen',
            text='No period provided, cannot phase fold lightcurve',
            theme=plot_theme,
        )

        fig2.add_layout(label)

    fig2.toolbar.logo = None
    fig2.yaxis.axis_label = 'Flux'
    fig2.xaxis.axis_label = 'Phase'
    fig2.yaxis.axis_label_text_font_size = '10pt'
    fig2.xaxis.axis_label_text_font_size = '10pt'
    fig2.min_border = 5

    apply_bokeh_figure_theme(fig1, plot_theme)
    apply_bokeh_figure_theme(fig2, plot_theme)

    return fig1, fig2


def plot_sed(star_id, project=None, *, theme=None):
    plot_theme = resolve_bokeh_theme(theme)

    star = Star.objects.select_related('project').get(pk=star_id)
    from AOTS.project_scoping import assert_plot_belongs_to_project
    assert_plot_belongs_to_project(star, project)
    photometry = star.photometry_set.all()

    data = []

    for p in photometry:

        if p.band not in zeropoints:
            continue

        zp = zeropoints[p.band]
        system = p.band.split('.')[0]

        flux = zp * 10 ** (-p.measurement / 2.5)

        data.append(dict(
            wave=p.wavelength,
            flux=flux,
            band=p.band,
            mag=p.measurement,
            err=p.error,
            system=system
        ))

    photd = pd.DataFrame(data)

    source = bpl.ColumnDataSource(photd)

    tools = [
        mpl.PanTool(),
        mpl.WheelZoomTool(),
        mpl.BoxZoomTool(),
        mpl.ResetTool()
    ]

    fig = bpl.figure(
        width=600,
        height=400,
        x_axis_type="log",
        y_axis_type="log",
        tools=tools
    )

    fig.toolbar.logo = None

    fig.yaxis.axis_label = "Flux"
    fig.xaxis.axis_label = "Wavelength (AA)"

    fig.yaxis.axis_label_text_font_size = "10pt"
    fig.xaxis.axis_label_text_font_size = "10pt"

    fig.min_border = 5

    if not data:
        fig.text(
            x=[0.5],
            y=[0.5],
            text=["No photometry available"],
            text_align="center",
            text_color=plot_theme.tick_text,
        )
        apply_bokeh_figure_theme(fig, plot_theme)
        return fig

    # invisible hover layer
    main_plot = fig.scatter(
        'wave',
        'flux',
        size=8,
        marker="circle",
        color='white',
        alpha=0.1,
        source=source,
        name="hover"
    )

    colors = SURVEY_PLOT_COLORS

    # plot per system
    for system, group in photd.groupby("system"):

        fig.scatter(
            group.wave,
            group.flux,
            marker="circle",
            size=9,
            color=colors.get(system, "black"),
            fill_alpha=0.3,
            line_alpha=1.0,
            line_width=1.5
        )

    hover = themed_field_hover_tool(
        renderers=[main_plot],
        tooltips=[
            ("band", "@band"),
            ("magnitude", "@mag ± @err"),
        ],
        theme=plot_theme,
    )

    fig.add_tools(hover)

    apply_bokeh_figure_theme(fig, plot_theme)

    return fig
