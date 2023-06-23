############################################################################
####                            Libraries                               ####
############################################################################

import os

import time

import sys

sys.path.append('/home/wedge/Uni/aots/src/AOTS/')
os.environ["DJANGO_SETTINGS_MODULE"] = "AOTS.settings"

import numpy as np

import django

django.setup()

from stars.models import Project
from analysis.models import DataSource

from astropy import units as u
from astropy.coordinates import SkyCoord

from astroquery.vizier import Vizier

############################################################################
####                          Configuration                             ####
############################################################################

#   Delete old parameter entries
rm_old_para = False

############################################################################
####                               Main                                 ####
############################################################################

if __name__ == '__main__':
    #   Load projects
    projects = Project.objects.all()

    #   Loop over projects
    for pro in projects:
        print()
        print(pro)

        #   Get stars
        stars = pro.star_set.all()

        for star in stars:
            print(f"\t{star.name}")

            #   Get coordinates
            ra = star.ra
            dec = star.dec

            coord = SkyCoord(ra=ra, dec=dec, unit=(u.deg, u.deg), frame='icrs')

            #   Check is parallax entry from GAIA DR3 exists -> skip if yes
            old_parall = star.parameter_set.filter(name__exact='parallax')
            conti = False
            for old in old_parall:
                source_name = old.data_source.name
                if source_name == 'Gaia DR3':
                    conti = True
            if conti:
                print('\tSkip star')
                continue

            #   Get GAIA data
            gaia_data = Vizier(
                catalog='I/355/gaiadr3',
                columns=['Plx', 'e_Plx', 'pmRA', 'e_pmRA', 'pmDE', 'e_pmDE',
                         'Gmag', 'e_Gmag', 'BPmag', 'e_BPmag', 'RPmag',
                         'e_RPmag'],
            ).query_region(coord, radius=1 * u.arcsec)

            #   Check if GAIA request contains data
            if gaia_data and len(gaia_data[0]) == 1:
                print('\tAdd phtometry')
                mags = ['Gmag', 'BPmag', 'RPmag']
                errs = ['e_Gmag', 'e_BPmag', 'e_RPmag']
                bands = ['GAIA3.G', 'GAIA3.BP', 'GAIA3.RP']
                for band, mag, err in zip(bands, mags, errs):
                    #   Skip in case of invalid magnitude
                    if np.isnan(gaia_data[0][mag]): continue

                    #   Add magnitude
                    star.photometry_set.create(
                        band=band,
                        measurement=gaia_data[0][mag],
                        error=gaia_data[0][err],
                        unit='mag',
                    )

                print('\tUpdate/Add parallax and proper motion')
                try:
                    dsgaia = DataSource.objects.get(
                        name__exact='Gaia DR3',
                        project=pro,
                    )
                except DataSource.DoesNotExist:
                    dsgaia = DataSource.objects.create(
                        name='Gaia DR3',
                        note='3nd Gaia data release',
                        reference='https://doi.org/10.1051/0004-6361/202243940',
                        project=pro,
                    )

                #   Set parallax
                if (str(gaia_data[0]['Plx']) != '--' and
                        str(gaia_data[0]['e_Plx']) != '--'):
                    for old in old_parall:
                        #   Delete old entries is requested
                        if rm_old_para:
                            print('\t\tDelete old parallax entry')
                            old.delete()
                        else:
                            #   Delete existing DR3 entries
                            source_name = old.data_source.name
                            if source_name == 'Gaia DR3':
                                old.delete()

                    print('\t\tAdd new parallax entry')
                    star.parameter_set.create(
                        data_source=dsgaia,
                        name='parallax',
                        component=0,
                        value=gaia_data[0]['Plx'],
                        error=gaia_data[0]['e_Plx'],
                        unit='mas',
                    )

                #   RA proper motion
                if (str(gaia_data[0]['pmRA']) != '--' and
                        str(gaia_data[0]['e_pmRA']) != '--'):
                    old_pmra = star.parameter_set.filter(name__exact='pmra')
                    for old in old_pmra:
                        #   Delete old entries is requested
                        if rm_old_para:
                            print('\t\tDelete old pmra entry')
                            old.delete()
                        else:
                            #   Delete existing DR3 entries
                            source_name = old.data_source.name
                            if source_name == 'Gaia DR3':
                                old.delete()

                    print('\t\tAdd new pmra entry')
                    star.parameter_set.create(
                        data_source=dsgaia,
                        name='pmra',
                        component=0,
                        value=gaia_data[0]['pmRA'],
                        error=gaia_data[0]['e_pmRA'],
                        unit='mas',
                    )

                #   DEC proper motion
                if (str(gaia_data[0]['pmDE']) != '--' and
                        str(gaia_data[0]['e_pmDE']) != '--'):
                    old_pmdec = star.parameter_set.filter(name__exact='pmdec')
                    for old in old_pmdec:
                        #   Delete old entries is requested
                        if rm_old_para:
                            print('\t\tDelete old pmdec entry')
                            old.delete()
                        else:
                            #   Delete existing DR3 entries
                            source_name = old.data_source.name
                            if source_name == 'Gaia DR3':
                                old.delete()

                    print('\t\tAdd new pmdec entry')
                    star.parameter_set.create(
                        data_source=dsgaia,
                        name='pmdec',
                        component=0,
                        value=gaia_data[0]['pmDE'],
                        error=gaia_data[0]['e_pmDE'],
                        unit='mas',
                    )

                print()

            #   Sleep for 5s to avoid hitting the Vizier-Server too often
            time.sleep(5.)
        # try:
        #     dsgaia_old = DataSource.objects.get(
        #         name__exact='Gaia EDR3',
        #         project=pro,
        #     )
        #     dsgaia_old.delete()
        #     print('Gaia EDR3 datasouce deleted')
        # except:
        #     print('Gaia EDR3 datasouce not found or deletion failed')
