############################################################################
####                            Libraries                               ####
############################################################################

import os

os.environ["DJANGO_SETTINGS_MODULE"] = "AOTS.settings"

import django

django.setup()

import numpy as np

from astropy import units as u
import astropy.coordinates as coord
from astropy.coordinates import SkyCoord, Galactic

import matplotlib as mpl
import matplotlib.pyplot as plt

from stars.models import Project


############################################################################
####                            Functions                               ####
############################################################################

def coordinates_aitoff_plot(coords):
    '''
        Plot object positions using aitoff projection

        Parameters
        ----------
            coords          : `astropy.coordinates.SkyCoord` object

        Returns
        -------
            fig, ax         : `matplotlib.pyplot.subplots` figure and axes obj.
    '''
    #   Initialize Plot
    fig, ax = plt.subplots(
        figsize=(10, 5),
        subplot_kw=dict(projection="aitoff"),
    )

    #   Convert coordinates
    sph = coords.spherical

    #   Scatter plot
    cs = ax.scatter(
        -sph.lon.wrap_at(180 * u.deg).radian,
        sph.lat.radian,
        c=sph.distance.value,
        s=10.,
    )

    #   Define ticks
    def fmt_func(x, pos):
        val = coord.Angle(-x * u.radian).wrap_at(360 * u.deg).degree
        return f'${val:.0f}' + r'^{\circ}$'

    ticker = mpl.ticker.FuncFormatter(fmt_func)
    ax.xaxis.set_major_formatter(ticker)

    #   Add grid
    ax.grid()

    #   Add color bar
    cb = fig.colorbar(cs)
    cb.set_label(f'Distance [{sph.distance.unit.to_string()}]')

    return fig, ax


############################################################################
####                               Main                                 ####
############################################################################

if __name__ == '__main__':
    #   Load projects
    projects = Project.objects.all()

    #   Make a plots for each project
    for pro in projects:
        print()
        print(pro)

        #   Get stars
        stars = pro.star_set.all()
        nstars = len(stars)

        #   Get coordinates and GAIA DR3 parallax from each system
        ra = np.zeros(nstars)
        dec = np.zeros(nstars)
        # para = np.ones(nstars) * 0.0001
        para = np.zeros(nstars)
        for i, star in enumerate(stars):
            #   Get coordinates
            ra[i] = star.ra
            dec[i] = star.dec

            #   Get parallax entries
            parallaxes = star.parameter_set.filter(name__exact='parallax')

            #   Restrict to DR3
            for p in parallaxes:
                source_name = p.data_source.name
                if source_name == 'Gaia DR3':
                    para[i] = p.value

        # #   Get coordinates
        # coordinates = pro.star_set.values_list('ra', 'dec')

        #   Add units
        ra = ra * u.deg
        dec = dec * u.deg
        para = para / 1000 * u.arcsec

        #   Calculate distance
        distance = para.to_value(u.kpc, equivalencies=u.parallax()) * u.kpc

        #   Remove bad entries/clear distance array
        mask = np.isinf(distance)
        distance[mask] = 0.

        #   Set up SkyCoord object
        sky_coordinates = SkyCoord(
            ra=ra,
            dec=dec,
            distance=distance,
            frame='icrs',
        )

        #   Plot figures
        # fig, ax = coordinates_aitoff_plot(sky_coordinates)
        # ax.set_xlabel('RA [deg]')
        # ax.set_ylabel('Dec [deg]')
        # plt.show()

        sky_coordinates_gal = sky_coordinates.transform_to(Galactic())
        fig, ax = coordinates_aitoff_plot(sky_coordinates_gal);
        # ax.set_xlabel(r'Galactic longitude, $l$ [deg]')
        # ax.set_ylabel(r'Galactic latitude, $b$ [deg]')
        ax.set_xlabel('Galactic longitude [deg]')
        ax.set_ylabel('Galactic latitude [deg]')
        plt.savefig(
            f'media/aitoff_projections/{pro.slug}_galactic.png',
            bbox_inches='tight',
            format='png',
        )
        # plt.show()
