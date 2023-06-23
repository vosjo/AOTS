import os

import sys

sys.path.append('../')
os.environ["DJANGO_SETTINGS_MODULE"] = "AOTS.settings"

import django

django.setup()

from stars.models import Project
from observations.models import Observatory

import pandas as pd

data = pd.read_csv('observatories.csv', low_memory=False)

data['url'] = data['url'].astype(str)
data['weatherurl'] = data['weatherurl'].astype(str)
data['note'] = data['note'].astype(str)

target_project = 'Project RGB'
# target_project = 'Test Project'

try:
    project = Project.objects.get(name__exact=target_project)
    print(project)

    for index, obs in data.iterrows():
        lat = float(obs['lat'])
        lon = float(obs['long'])
        url = obs['url'] if not 'nan' in obs['url'] else ''
        weatherurl = obs['weatherurl'] if not 'nan' in obs['weatherurl'] else ''
        note = obs['note'] if not 'nan' in obs['note'] else ''

        o = Observatory.objects.filter(latitude__range=(lat - 0.1, lat + 0.1),
                                       longitude__range=(lon - 0.1, lon + 0.1),
                                       project__exact=project)

        if len(o) > 0:
            o = o[0]
            o.project = project
            o.name = obs['Name']
            o.telescopes = obs['Telescopes']
            o.latitude = lat
            o.longitude = lon
            o.altitude = obs['alt']
            o.space_craft = obs['space']
            o.url = url
            o.weatherurl = weatherurl
            o.note = note
            o.save()
            print(o)
            continue

        o = Observatory(project=project, name=obs['Name'], telescopes=obs['Telescopes'],
                        latitude=lat, longitude=lon, altitude=obs['alt'], space_craft=obs['space'],
                        url=url, weatherurl=weatherurl, note=note)
        o.save()
        print(o)

except Project.DoesNotExist:
    print('ERROR: project not found -> exit')
