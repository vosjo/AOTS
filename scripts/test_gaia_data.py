
from astroquery.gaia import Gaia
from astropy.table import QTable

import matplotlib.pyplot as plt

import numpy as np

# query_text = '''SELECT TOP 4096 phot_g_mean_mag, phot_bp_mean_mag, phot_rp_mean_mag
# FROM gaiadr3.gaia_source
# ORDER BY random_index
# '''

# query_text = '''SELECT source_id, FLOOR((phot_g_mean_mag+5.0*log10(parallax)-10.0) * 10) AS g_mag_abs_index, FLOOR(bp_rp * 10) as bp_rp_index
# FROM gaiadr3.gaia_source
# WHERE parallax_over_error >= 5
# AND phot_bp_mean_flux_over_error > 0
# AND phot_rp_mean_flux_over_error > 0
# AND SQRT(POWER(2.5/log(10) / phot_bp_mean_flux_over_error, 2) + POWER(2.5/log(10) / phot_rp_mean_flux_over_error, 2)) <= 0.05
# AND random_index BETWEEN 0 AND 1000000
# '''


query_text = '''SELECT source_id, phot_g_mean_mag + 5.0 * log10(parallax) - 10.0 as g_mag_abs, bp_rp
FROM gaiadr3.gaia_source
WHERE parallax_over_error >= 80
AND phot_bp_mean_flux_over_error > 0
AND phot_rp_mean_flux_over_error > 0
AND SQRT(POWER(2.5/log(10) / phot_bp_mean_flux_over_error, 2) + POWER(2.5/log(10) / phot_rp_mean_flux_over_error, 2)) <= 0.03
AND random_index BETWEEN 0 AND 3000000
'''

job = Gaia.launch_job_async(query_text)
# job = Gaia.launch_job(query_text)
gaia_data = job.get_results()

print(len(gaia_data))
print(gaia_data[:4])

gaia_data.write('gaia_data.fits', overwrite=True)

# gaia_data = QTable.read('gaia_data.fits')

# print(dir(gaia_data['phot_g_mean_mag'][:4]))
# print(gaia_data['phot_g_mean_mag'][:4].value)


fig = plt.figure(figsize=(20,20))

# mag_filt = gaia_data['phot_g_mean_mag'].value
# color = gaia_data['phot_bp_mean_mag'].value - gaia_data['phot_rp_mean_mag'].value
mag_filt = gaia_data['g_mag_abs'].value
color = gaia_data['bp_rp'].value

plt.ylim([float(np.max(mag_filt))+0.5,float(np.min(mag_filt))-0.5])

plt.scatter(color, mag_filt)

plt.show()
