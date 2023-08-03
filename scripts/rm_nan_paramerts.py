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

from analysis.models import Parameter

############################################################################
####                               Main                                 ####
############################################################################

if __name__ == '__main__':
    #   Load parameters
    parameters = Parameter.objects.all()

    #   Loop over projects
    for para in parameters:
        if np.isnan(para.value):
            # print(para)
            print(para.star)
            print(para.value)
            para.delete()

