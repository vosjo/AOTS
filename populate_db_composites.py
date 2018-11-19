
import os
os.environ["DJANGO_SETTINGS_MODULE"] = "BiMoT.settings"

import django
django.setup()

import numpy as np

from stars.models import Project, Star, Tag
from analysis.models import DataSource, Parameter

import pandas as pd

from astropy.coordinates import Angle

data = pd.read_csv('observed_systems.csv')
data['Note'] = data['Note'].astype(str)

print (data)
    
#-- create a new project
try:
   project = Project.objects.get(name__exact='Composite sdBs')
except Project.DoesNotExist:
   project = Project.objects.create(name='Composite sdBs', description='Radial velocity monitoring of long period sdB+MS binaries')


#-- delete all systems in the database for this project
for star in Star.objects.filter(project__exact=project.pk):
    star.delete() 

#-- make UVES and HERMES tags
try: 
    tuves = Tag.objects.get(name__exact='UVES')
except Tag.DoesNotExist:
    tuves = Tag.objects.create(name='UVES', project=project, description='UVES spectrocopy target', color='#1E90FF')

try: 
    thermes = Tag.objects.get(name__exact='HERMES')
except Tag.DoesNotExist:
    thermes = Tag.objects.create(name='HERMES', project=project, description='HERMES spectrocopy target', color='#1D8B2E')

try: 
    tchiron = Tag.objects.get(name__exact='CHIRON')
except Tag.DoesNotExist:
    tchiron = Tag.objects.create(name='CHIRON', project=project, description='CHIRON spectrocopy target', color='#8E44AD')



#-- create GAIA DR2 datasource 
try: 
    dsgaia = DataSource.objects.get(name__exact='Gaia DR 2')
except DataSource.DoesNotExist:
    dsgaia = DataSource.objects.create(name='Gaia DR 2', note='2nd Gaia data release', reference='https://doi.org/10.1051/0004-6361/201833051', project=project)




#-- Add the spectroscopically confirmed composite sdB binaries
for index, star in data.iterrows():

    note = star['Note']
    if 'nan' in note: note = ''

    name = star['name'].strip()

    #-- add system to database
    s = Star(name=name, project=project, ra=star['RA_gaia'], dec=star['Dec_gaia'], classification=star['class'],
                classification_type='SP', note=note)
    s.save()


    print( name, note )

    passbands = ['GAIA2.G', 'GAIA2.BP', 'GAIA2.RP']
    units = ['mag', 'mag', 'mag']

    for b, pb, u in zip(['G', 'BP', 'RP'], passbands, units):
        
        if np.isnan(star[b]): continue
        #err = 0.0 if np.isnan(star['e_'+b]) else star['e_'+b]
        
        print( pb, ':', star[b] )
        
        s.photometry_set.create(band=pb, measurement=star[b], error=0.01, unit=u)
        

        
    #-- check if UVES/HERMES observations exist, and add tag
    if 'UVES' in star['spectrograph']:
        print( 'UVES' )
        s.tags.add(tuves.pk)
        s.observing_status='ON'
        s.save()

    if 'CHIRON' in star['spectrograph']:
        print( 'CHIRON' )
        s.tags.add(tchiron.pk)
        s.observing_status='ON'
        s.save()

    if 'HERMES' in star['spectrograph']:
        print( 'HERMES' )
        s.tags.add(thermes.pk)
        if name == 'BD-11162' or name == 'Feige 80':
            s.observing_status='ON'
        else:
            s.observing_status='FI'
        s.save()
        
    #-- add parameters from gaia DR2
    
    s.parameter_set.create(data_source=dsgaia, name='parallax', component=0, value=star['parallax'], error=star['parallax_error'], unit='')
    
    s.parameter_set.create(data_source=dsgaia, name='pmra', component=0, value=star['pmra'], error=star['pmra_error'], unit='mas')
    
    s.parameter_set.create(data_source=dsgaia, name='pmdec', component=0, value=star['pmdec'], error=star['pmdec_error'], unit='mas')



