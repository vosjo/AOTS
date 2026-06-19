############################################################################
####  Thin CLI wrapper around stars.services.gaia_import (Gaia DR3 import) ####
############################################################################

import os
import sys
import time

sys.path.append('../')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AOTS.settings')

import django

django.setup()

from stars.models import Project
from stars.services.gaia_import import import_gaia_dr3_for_star

############################################################################
####                          Configuration                             ####
############################################################################

# Skip stars that already have Gaia DR3 parallax (legacy batch behaviour).
skip_if_dr3_parallax = True

# Pause between Vizier queries (seconds).
delay_seconds = 5.0

############################################################################
####                               Main                                 ####
############################################################################

if __name__ == '__main__':
    for project in Project.objects.all():
        print(project)
        for star in project.star_set.all():
            print(f'\t{star.name}')

            if skip_if_dr3_parallax:
                has_dr3 = star.parameter_set.filter(
                    name='parallax',
                    parameter_source__name='Gaia DR3',
                ).exists()
                if has_dr3:
                    print('\tSkip star (Gaia DR3 parallax already present)')
                    continue

            result = import_gaia_dr3_for_star(star)
            print(f'\t{result.status}: {result.message}')
            if result.warnings:
                for warning in result.warnings:
                    print(f'\t\tWarning: {warning}')

            time.sleep(delay_seconds)
