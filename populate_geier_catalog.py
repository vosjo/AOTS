 
import os
os.environ["DJANGO_SETTINGS_MODULE"] = "BiMoT.settings"

import django
django.setup()

import numpy as np
 
from stars.models import Star, Tag
from analysis.aux import fileio

import numpy as np
import pandas as pd
data = pd.read_csv('/home/joris/drive/Catalog/close_targets.csv', low_memory=False)

photbands = ['FUV_GALEX', 'NUV_GALEX', 'F_GSC', 'Bj_GSC', 'V_GSC', 'N_GSC', 'B_GSC', 'V_APASS', 'B_APASS', 'g_APASS', 'r_APASS', 'I_APASS', 'u_SDSS', 'g_SDSS', 'r_SDSS', 'I_SDSS', 'z_SDSS', 'u_VST', 'g_VST', 'r_VST', 'I_VST', 'z_VST', 'u_SKYM', 'v_SKYM', 'g_SKYM', 'r_SKYM', 'i_SKYM', 'z_SKYM', 'g_PS1', 'r_PS1', 'i_PS1', 'z_PS1', 'y_PS1', 'J_2MASS', 'H_2MASS', 'K_2MASS', 'Y_UKIDSS', 'J_UKIDSS', 'H_UKIDSS', 'K_UKIDSS', 'Z_VISTA', 'Y_VISTA', 'J_VISTA', 'H_VISTA', 'Ks_VISTA', 'W1', 'W2', 'W3', 'W4']



#data = data.ix[0:10]

#print data

try: 
   tgeier = Tag.objects.get(name__exact='SDCAT')
except Tag.DoesNotExist:
   tgeier = Tag.objects.create(name='SDCAT', description='Geier+2017 subdwarf catalog', color='#93004A')

for i in range(10):
   
   star = data.ix[i]
   
   #print star
   
   ## Add star
   #s = Star(name=star['name'], ra=star['RA'], dec=star['Dec'], classification=star['spec_class'],
            #classification_type='SP', note=star['Reference'])
   #s.save()
   
   
   ## Add tag
   #s.tags.add(tgeier.pk)
   #s.save()
   
   
   #Add photometry
   
   for b in photbands:
      
      if np.isnan(float(star[b])): continue
      
      if 'e_'+b in star:
         err = 0.0 if np.isnan(float(star['e_'+b])) else star['e_'+b]
      else:
         err = 0.0
      
   
      #s.photometry_set.create(band=b, measurement=star[b], error=err, unit='mag')
      
   
   sys.exit()