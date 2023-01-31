import os

os.environ["DJANGO_SETTINGS_MODULE"] = "AOTS.settings"

import django

django.setup()

from stars.models import Project
from observations.auxil.read_spectrum import (
    derive_spectrum_info,
    derive_specfile_info,
)

##  Delete all systems in database
# for star in Star.objects.all():
# star.delete()

#   Load projects
projects = Project.objects.all()

#   Loop over projects
for pro in projects:
    print()
    print(pro)

    #   Load spectra
    spectra = pro.spectrum_set.all()

    #   Loop over spectra
    for spec in spectra:
        #   Load specfiles
        specfiles = spec.specfile_set.all()

        #   Loop over specfiles
        for spf in specfiles:
            #   Get SpecFile pk
            spf_pk = spf.pk

            print('    ', spf)

            #   Update SpecFile information
            message, success = derive_specfile_info(spf_pk, user_info)
            print('    ', message, success)
