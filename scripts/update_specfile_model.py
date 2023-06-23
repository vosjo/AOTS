import os

import sys

sys.path.append('../')
os.environ["DJANGO_SETTINGS_MODULE"] = "AOTS.settings"

import django

django.setup()

from stars.models import Project
from observations.auxil.read_spectrum import (
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
        #   Get spectrum pk
        spec_pk = spec.pk

        #   Get user provided data
        user_info = spec.userinfo_set.all()

        #   Check that only one set of user data exists
        if len(user_info) != 1:
            user_info = {}
        else:
            #   Extract data from UserInfo instance
            user_info = user_info.values()[0]

            #   Clean user data -  remove defaults
            __dict = {}
            for key, value in user_info.items():
                if value != -1. and value != '':
                    __dict[key] = value
            user_info = __dict

        print()
        print('    ', spec)

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
