############################################################################
####                            Libraries                               ####
############################################################################

import os

import time

import sys

sys.path.append('../')
os.environ["DJANGO_SETTINGS_MODULE"] = "AOTS.settings"

import numpy as np

import django

django.setup()

from stars.models import Project
from analysis.models import DataSource

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

            #   Check if parallax entry from GAIA DR3 exists
            parallaxes = star.parameter_set.filter(name__exact='parallax')
            conti = False
            for para in parallaxes:
                source_name = para.data_source.name
                if source_name == 'Gaia DR3':
                    conti = True
                    dr3_para = para
            if not conti:
                print('\t\tSkip star due to missing DR3 parallax')
                continue

            #   Get parallax and error
            para_value = dr3_para.value
            para_err = dr3_para.error

            if para_err > 0.1:
                print('\t\tSkip star due to a too high parallax error')
                continue

            #   Check if Gaia Gmag is available
            gmag = star.photometry_set.filter(band__exact='GAIA3.G')

            if not gmag:
                print('\t\tSkip star due to missing Gaia G magnitude')
                continue

            #   Get Gaia photometry
            gmag = gmag[0]
            gmag_value = gmag.measurement
            gmag_err = gmag.error

            #   Calculate absolute magnitude
            gmag_abs = gmag_value + 5.0 * np.log10(para_value) - 10.0
            gmag_abs_err = (gmag_err**2 + (para_err / para_value)**2)**(0.5)

            #   Look for old entries, delete those and add new values
            old_abs_mag = star.parameter_set.filter(name__exact='absolute_g_mag')
            for old in old_abs_mag:
                print('\t\tDelete old absolute Gaia magnitude entry')
                old.delete()

            dsgaia = DataSource.objects.get(
                name__exact='Gaia DR3',
                project=pro,
            )

            print('\t\tAdd new absolute Gaia magnitude entry')
            star.parameter_set.create(
                data_source=dsgaia,
                name='absolute_g_mag',
                component=0,
                value=gmag_abs,
                error=gmag_abs_err,
                unit='mag',
            )

