############################################################################
####  Deprecated: absolute G mag is derived by update_stars_gaia-dr3.py   ####
####  (stars.services.gaia_import). Re-run Gaia import for each star.     ####
############################################################################

import os
import sys

sys.path.append('../')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AOTS.settings')

import django

django.setup()

from stars.models import Project
from stars.services.gaia_import import import_gaia_dr3_for_star

if __name__ == '__main__':
    for project in Project.objects.all():
        print(project)
        for star in project.star_set.all():
            has_dr3_parallax = star.parameter_set.filter(
                name='parallax',
                parameter_source__name='Gaia DR3',
            ).exists()
            if not has_dr3_parallax:
                print(f'\t{star.name}: skip (no Gaia DR3 parallax; run update_stars_gaia-dr3.py)')
                continue
            result = import_gaia_dr3_for_star(star)
            print(f'\t{star.name}: {result.status} — {result.message}')
