###  API spectra upload script ###

import requests

#   Set upload URL
URL = 'https://a15.astro.physik.uni-potsdam.de/api/observations/specfiles/'
URL = 'http://127.0.0.1:8000/api/observations/specfiles/'

#   Credentials
username = '?????'
password = '?????'

#   Get Project ID, e.g., from: http://127.0.0.1:8000/api/projects/
data = {'project': 2}

#   Path to file that should be uploaded
file_path = 'Brankica_spectra_20230110/HD48491_20200918.fit'

#   Read file
files = {'specfile': open(file_path, 'rb')}

#   Upload file
response = requests.post(URL, auth=(username, password), files=files, data=data)

#   Upload response code
print('Upload response code: ', dir(response))

#   Get PK/ID of the uploaded spectrum
pk = response.json()['pk']

#   Initialization of the spectrum processing
process_URL = f'{URL}{pk}/process/'
response = requests.post(process_URL, auth=(username, password))

#   Process response code
print('Process response code: ', response.status_code)
