import os

os.environ["DJANGO_SETTINGS_MODULE"] = "AOTS.settings"

import django

django.setup()

# from stars.models import Project, Star
from observations.models import RawSpecFile
from observations.auxil.read_spectrum import derive_rawfile_info

#   Load raw file instances
rawspecfiles = RawSpecFile.objects.all()

#   Loop over all instances
for raw in rawspecfiles:
    print('           ', raw)

    #   Get RawSpecFile pk
    raw_spf_pk = raw.pk

    #   Update SpecFile information
    message, success = derive_rawfile_info(raw_spf_pk)
    print('        ', message, success)

##   Load projects
# projects = Project.objects.all()

##   Loop over projects
# for pro in projects:
# print()
# print(pro)

##   Load spectra
# spectra = pro.spectrum_set.all()

##   Loop over spectra
# for spec in spectra:
##   Load specfiles
# specfiles = spec.specfile_set.all()

##   Loop over specfiles
# for spf in specfiles:
# print('        ', spf)

##   Load rawspecfiles
# rawspecfiles = spf.rawspecfile_set.all()

# for raw in rawspecfiles:
# print('           ', raw)

##   Get RawSpecFile pk
# raw_spf_pk = raw.pk

##   Update SpecFile information
# message, success = derive_rawfile_info(raw_spf_pk)
# print('        ', message, success)
