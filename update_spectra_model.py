import os
os.environ["DJANGO_SETTINGS_MODULE"] = "AOTS.settings"

import django
django.setup()

import numpy as np

from stars.models import Project, Star
from observations.auxil.read_spectrum import (
    derive_spectrum_info,
    derive_specfile_info,
    )


##  Delete all systems in database
#for star in Star.objects.all():
    #star.delete()

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
        spec_pk = spec.pk
        #spec_hjd = spec.hjd
        print()
        print('    ', spec)
        message, success = derive_spectrum_info(spec_pk)
        print('        ', message, success)

        #   Load specfiles
        specfiles = spec.specfile_set.all()

        #   Loop over specfiles
        for spf in specfiles:
            spf_pk = spf.pk
            #spf_hjd = spf.hjd
            print('        ', spf)
            message, success = derive_specfile_info(spf_pk)
            print('        ', message, success)
            #print('            Specfile updated')



















