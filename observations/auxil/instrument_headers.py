"""
Functions to derive essential information from the header in instrument specific cases.
"""

import numpy as np
from astropy.time import Time
from observations.models import Spectrum, Observatory

import astropy.units as u
from astropy.coordinates import EarthLocation
from astropy.coordinates.angles import Angle


def extract_header_info(header, user_info={}):
    """
    Reads the important header information and returns it as a dictionary
    """

    if 'ESO TEL ALT' in header:
        data = derive_eso_info(header)
    elif header.get('INSTRUME', '') == 'FEROS':
        data = derive_feros_info(header)
    elif header.get('INSTRUME', '') == 'HERMES':
        data = derive_hermes_info(header)
    elif header.get('INSTRUME', '') == 'SP_1.3m_MUSI':
        data = derive_MUSICOS_info(header)
    elif 'SBIG ST' in header.get('INSTRUME', ''):
        data = derive_baches_info(header)
    elif header.get('INSTRUME', '') in ['MODS1B', 'MODS1R', 'MODS2B', 'MODS2R']:
        data = derive_MODS_info(header)
    elif ('SOAR 4.1m' in header.get('TELESCOP', '') and
          'Goodman Spectro' in header.get('INSTRUME', '')):
        data = derive_soar_info(header)
    elif 'SDSS' in header.get('TELESCOP', ''):
        data = derive_SDSS_info(header)
    elif 'LAMOST' in header.get('TELESCOP', ''):
        data = derive_LAMOST_info(header)
    elif 'TESS' in header.get('TELESCOP', ''):
        data = derive_TESS_info(header)
    else:
        data = derive_generic_info(header)

    #-- update the data extracted from the header with data provided by the user
    if user_info is None:
        user_info = {}
    data.update(user_info)

    return data

def extract_header_raw(header, user_info={}):
    '''
    Set header data for raw file
    '''

    #   Read header & extract data
    data = derive_generic_raw(header)

    #   Set file type for OES/Ondrejov
    if data['instrument'] == 'OES':
        if data['filetype'] == 'object':
            data['filetype'] = 'Science'
        elif data['filetype'] == 'zero':
            data['filetype'] = 'Dark'
        elif data['filetype'] == 'flat':
            data['filetype'] = 'Flat'
        elif data['filetype'] == 'comp':
            data['filetype'] = 'Wavelength'

    #   Update the data extracted from the header with data provided by the user
    if user_info is None:
        user_info = {}
    data.update(user_info)

    return data

def get_observatory(header, project):
    """
        Finds a suitable observatory or if not possible, create a new one.
    """

    #   Maximum tolerable deviation in the coordinates
    #   -> a difference of 0.1 degree in latitude and longitude is roughly 10 km
    d = 0.1

    #    Try to find the observatory on name match
    if 'TELESCOP' in header:
        try:
            obs = Observatory.objects.get(
                telescopes__icontains = header['TELESCOP'],
                project__exact = project,
                )
            return obs
        except Exception as e:
            telescope = header.get('TELESCOP', 'UK')

    #   Try to find observatory on location match
    if 'OBSGEO-X' in header:
        x, y = header.get('OBSGEO-X', 0), header.get('OBSGEO-Y', 0)
        z    = header.get('OBSGEO-Z', 0)
        loc = EarthLocation.from_geocentric(x=x*u.m, y=y*u.m, z=z*u.m,)
    elif 'ESO TEL GEOLAT' in header:
        lat = header.get('ESO TEL GEOLAT', 0)
        lon = header.get('ESO TEL GEOLON', 0)
        alt = header.get('ESO TEL GEOELEV', 0)
        loc = EarthLocation.from_geodetic(
            lat=lat*u.deg,
            lon=lon*u.deg,
            height=alt*u.m,
            )
    elif 'GEOLAT' in header:
        lat, lon = header.get('GEOLAT', 0), header.get('GEOLON', 0)
        alt      = header.get('GEOALT', 0)
        loc = EarthLocation.from_geodetic(
            lat=lat*u.deg,
            lon=lon*u.deg,
            height=alt*u.m,
            )
    elif 'SITELAT' in header and 'SITELONG' in header:
        lat = Angle(header.get('SITELAT', 0).strip(), unit='degree').degree
        lon = Angle(header.get('SITELONG', 0).strip(), unit='degree').degree
        alt = 0.
        loc = EarthLocation.from_geodetic(
            lat=lat*u.deg,
            lon=lon*u.deg,
            height=alt*u.m,
            )
    elif 'LATITUDE' in header and 'LONGITUD' in header:
        lat, lon = header.get('LATITUDE', 0), header.get('LONGITUD', 0)
        alt      = header.get('ELEVATIO', 0)
        loc = EarthLocation.from_geodetic(
            lat=lat*u.deg,
            lon=lon*u.deg,
            height=alt*u.m,
            )
    else:
        loc = EarthLocation.from_geodetic(
            lat=0*u.deg,
            lon=0*u.deg,
            height=0*u.m,
            )

    #   We look for an observatory that is within 1 degree from location stored
    #   in the header, altitude is not checked.
    obs = Observatory.objects.filter(
        latitude__range = (loc.lat.degree-d, loc.lat.degree+d),
        longitude__range = (loc.lon.degree-d, loc.lon.degree+d),
        project__exact = project,
        )

    if len(obs) > 0:
        return obs[0]

    #   If still no observatory exists, create a new one.
    obs = Observatory(
        name=telescope,
        latitude=loc.lat.degree,
        longitude=loc.lon.degree,
        altitude=loc.height.value,
        project=project,
        )
    obs.save()

    return obs


def derive_generic_info(header):
    """
    Tries to read some basic information from a unknown spectrum

    This information is stored in the spectrum database entry
    """

    data = {}

    #   HJD
    if 'HJD' in header:
        data['hjd'] = header['HJD']
    elif 'BJD' in header:
        data['hjd'] = header['BJD']
    elif 'MJD' in header:
        data['hjd'] = Time(header.get('MJD', 0.0), format='mjd', scale='utc').jd
    elif 'DATE-OBS' in header:
        date        = header.get('DATE-OBS', '2000-00-00')
        if 'T' not in date:
            if 'UT' in header:
                ut          = header.get('UT', '00:00:00.0')
                data['hjd'] = Time(date+'T'+ut, format='fits').jd
        else:
            data['hjd'] = Time(
                header.get('DATE-OBS', '2000-00-00T00:00:00.0Z'),
                format='fits'
                ).jd
    else:
        data['hjd'] = 2400000

    #   Pointing info
    data['objectname'] = header.get('OBJECT', '')

    try:
        data['ra'] = float(header.get('RA', 0.))
    except Exception:
        data['ra'] = Angle(header.get('RA', 0.), unit='hour').degree

    try:
        data['dec'] = float(header.get('DEC', 0.))
    except Exception:
        data['dec'] = Angle(header.get('DEC', 0.), unit='degree').degree

    #   Telescope and instrument info
    data['instrument'] = header.get('INSTRUME', 'UK')
    data['telescope'] = header.get('TELESCOP', 'UK')
    data['exptime'] = np.round(header.get('EXPTIME', -1), 0)
    data['observer'] = header.get('OBSERVER', 'UK')

    data['resolution'] = header.get('SPEC_RES', -1)
    data['snr'] = header.get('SNR', -1)
    data['seeing'] = header.get('SEEING', -1)

    data['filetype'] = 'UK'

    return data

def derive_generic_raw(header):
    """
    Tries to read some basic information from a unknown raw data files
    """

    data = {}

    #   HJD
    if 'HJD' in header:
        data['hjd'] = header['HJD']
    elif 'BJD' in header:
        data['hjd'] = header['BJD']
    elif 'MJD' in header:
        data['hjd'] = Time(header.get('MJD', 0.0), format='mjd', scale='utc').jd
    elif 'DATE-OBS' in header:
        date        = header.get('DATE-OBS', '2000-00-00')
        if 'T' not in date:
            if 'UT' in header:
                ut          = header.get('UT', '00:00:00.0')
                data['hjd'] = Time(date+'T'+ut, format='fits').jd
        else:
            data['hjd'] = Time(
                header.get('DATE-OBS', '2000-00-00T00:00:00.0Z'),
                format='fits'
                ).jd
    else:
        data['hjd'] = 2400000

    #if 'DATE-OBS' in header:
        #data['date-obs'] = header.get('DATE-OBS', '2000-00-00')
    #else:
        #data['date-obs'] = Time(data['hjd'], format='jd', precision=0).iso

    #   Pointing info
    data['objectname'] = header.get('OBJECT', '')

    #   Telescope and instrument info
    data['instrument'] = header.get('INSTRUME', 'UK')
    data['telescope']  = header.get('TELESCOP', 'UK')
    data['exptime']    = np.round(header.get('EXPTIME', -1), 0)
    data['observer']   = header.get('OBSERVER', 'UK')

    #   Tyr to find information on flat/bias/darks here
    data['filetype'] = header.get('IMAGETYP', 'UK')

    return data


def derive_soar_info(header):
    """
    Tries to read some basic information from a unknown spectrum

    This information is stored in the spectrum database entry
    """

    data = {}

    #   HJD
    if 'DATE-OBS' in header:
        date        = header.get('DATE-OBS', '2000-00-00')
        if 'T' not in date:
            if 'UT' in header:
                ut          = header.get('UT', '00:00:00.0')
                data['hjd'] = Time(date+'T'+ut, format='fits').jd
        else:
            data['hjd'] = Time(
                header.get('DATE-OBS', '2000-00-00T00:00:00.0Z'),
                format='fits'
                ).jd
    else:
        data['hjd'] = 2400000

    #   Pointing info
    data['objectname'] = header.get('OBJECT', '')

    data['ra'] = Angle(header.get('RA', 0.), unit='hour').degree
    data['dec'] = Angle(header.get('DEC', 0.), unit='degree').degree

    #   Telescope and instrument info
    data['instrument'] = header.get('INSTRUME', 'UK')
    data['telescope'] = header.get('TELESCOP', 'UK')
    data['exptime'] = np.round(header.get('EXPTIME', -1), 0)
    data['observer'] = header.get('OBSERVER', 'UK')

    data['seeing'] = header.get('SEEING', -1)
    data['airmass'] = header.get('AIRMASS', -1)

    data['fluxcal']      = True
    data['filetype'] = header.get('INSTCONF', 'UK')

    return data


def derive_eso_info(header):
   """
   Reads header information from a standard ESO fits file
   """

   data = {}

   # HJD
   data['hjd'] = Time(header.get('MJD-OBS', 0.0), format='mjd', scale='utc').jd

   # pointing info
   data['objectname'] = header.get('OBJECT', '')
   data['ra'] = header.get('RA', -1)
   data['dec'] = header.get('DEC', -1)
   data['alt'] = header.get('ESO TEL ALT', -1)
   data['az'] = header.get('ESO TEL AZ', -1)
   data['airmass'] = header.get('ESO TEL AIRM END', -1)

   # telescope and instrument info
   data['instrument']   = header.get('INSTRUME', 'UK')
   data['telescope']    = header.get('TELESCOP', 'UK')
   data['exptime']      = np.round(header.get('EXPTIME', -1), 0)
   data['barycor']      = header.get('ESO QC VRAD BARYCOR', -1)
   data['barycor_bool'] = False
   data['observer']     = header.get('OBSERVER', 'UK')
   data['filetype']     = header['PIPEFILE'].replace(".fits", "")

   if 'SPEC_RES' in header:
      data['resolution'] = header['SPEC_RES']
   elif 'UVES' in header.get('INSTRUME', 'UK'):
      data['resolution'] = 40000

   data['snr'] = header.get('SNR', -1)

   if data['instrument'] == 'XSHOOTER':
      data['fluxcal'] = True

   # observing conditions
   data['wind_speed'] = np.round(header.get('ESO TEL AMBI WINDSP', -1), 1)
   data['wind_direction'] = np.round(header.get('ESO TEL AMBI WINDDIR', -1), 0)
   if 'ESO TEL AMBI FWHM END' in header and 'ESO TEL AMBI FWHM START' in header:
      data['seeing'] = np.average([header.get('ESO TEL AMBI FWHM END', -1), header.get('ESO TEL AMBI FWHM START', -1)])
   elif 'ESO TEL AMBI FWHM START' in header:
      data['seeing'] = header.get('ESO TEL AMBI FWHM START', -1)
   elif 'ESO TEL AMBI FWHM END' in header:
      data['seeing'] = header.get('ESO TEL AMBI FWHM END', -1)

   return data

def derive_feros_info(header):
   """
   Read header information from a FEROS spectrum

   This information is stored in the spectrum database entry
   """

   data = {}

   # HJD
   data['hjd'] = Time(header.get('MJD-OBS', 0.0), format='mjd', scale='utc').jd

   # pointing info
   data['objectname'] = header.get('OBJECT', '')
   data['ra'] = header.get('RA', -1)
   data['dec'] = header.get('DEC', -1)
   data['alt'] = header.get('ESO TEL ALT', -1)
   data['az'] = header.get('ESO TEL AZ', -1)
   data['airmass'] = header.get('ESO TEL AIRM END', -1)

   # telescope and instrument info
   data['instrument']   = header.get('INSTRUME', 'UK')
   data['telescope']    = header.get('TELESCOP', 'UK')
   data['exptime']      = np.round(header.get('EXPTIME', -1), 0)
   data['resolution']   = 48000
   data['observer']     = header.get('OBSERVER', 'UK')
   data['filetype']     = header['PIPEFILE']

   # observing conditions
   data['wind_speed'] = np.round(header.get('ESO TEL AMBI WINDSP', -1), 1)
   data['wind_direction'] = np.round(header.get('ESO TEL AMBI WINDDIR', -1), 0)

   return data


def derive_MODS_info(header):
    """
    Read header information from a FEROS spectrum

    This information is stored in the spectrum database entry
    """

    data = {}

    #   HJD
    data['hjd'] = Time(header.get('MJD-OBS', 0.0), format='mjd', scale='utc').jd

    #   Pointing info
    data['objectname'] = header.get('OBJECT', '')
    data['ra'] = Angle(header.get('OBJRA', None), unit='hour').degree
    data['dec'] = Angle(header.get('OBJDEC', None), unit='degree').degree
    data['alt'] = header.get('TELALT', -1)
    data['az'] = header.get('TELAZ', -1)
    data['airmass'] = header.get('AIRMASS', -1)

    #   Telescope and instrument info
    data['instrument'] = header.get('INSTRUME', 'UK')
    data['telescope']  = header.get('TELESCOP', 'UK')
    data['exptime']    = np.round(header.get('EXPTIME', -1), 0)
    if header.get('MASKNAME', '') == 'LS5x60x0.6':
        if header.get('GRATNAME', '').strip() == 'G400L':
            data['resolution'] = 1850
        elif header.get('GRATNAME', '').strip() == 'G670L':
            data['resolution'] = 2300
    data['observer']     = header.get('OBSERVER', 'UK')
    data['filetype']     = 'MODS_final_' + header.get('GRATNAME', '').strip()
    data['fluxcal']      = True

    return data


def derive_hermes_info(header):
   """
   Read header information from a HERMES spectrum

   This information is stored in the spectrum database entry
   """

   data = {}

   # HJD
   data['hjd'] = header.get('BJD', 2400000)

   # pointing info
   data['objectname'] = header.get('OBJECT', '')
   data['ra'] = float(header.get('RA', -1))
   data['dec'] = float(header.get('DEC', -1))
   data['alt'] = float(header.get('TELALT', -1))
   data['az'] = float(header.get('TELAZI', -1))
   data['airmass'] = -1

   # telescope and instrument info
   data['instrument']   = header.get('INSTRUME', 'UK')
   data['telescope']    = header.get('TELESCOP', 'UK')
   data['exptime']      = np.round(header.get('EXPTIME', -1), 0)
   data['resolution']   = 85000
   data['barycor']      = header.get('BVCOR', -1)
   data['barycor_bool'] = True
   data['observer']     = header.get('OBSERVER', 'UK')
   data['filetype']     = 'MERGE_REBIN'

   return data


def derive_SDSS_info(header):
   """
   Read header information from an SDSS spectrum

   This information is stored in the spectrum database entry
   """

   data = {}

   # HJD
   if 'TAI' in header:
      t = Time('1858-11-17', format='iso') + header.get('TAI', 0.0) * u.second
      data['hjd'] = t.jd
   elif 'MJD' in header:
      data['hjd'] = Time(header.get('MJD', 0.0), format='mjd', scale='utc').jd
   else:
      data['hjd'] = 2400000

   # pointing info
   if 'SPEC_ID' in header:
      data['objectname'] = header.get('SPEC_ID', '')
   else:
      ra_ = "J{:02.0f}{:02.0f}{:05.2f}".format(*Angle(header.get('PLUG_RA', -1), unit='degree').hms)
      dec_ = Angle(header.get('PLUG_DEC', -1), unit='degree').dms
      data['objectname'] = ra_ + "{:+03.0f}{:02.0f}{:05.2f}".format(dec_[0], abs(dec_[1]), abs(dec_[2]))

   data['ra'] = header.get('PLUG_RA', -1)
   data['dec'] = header.get('PLUG_DEC', -1)

   # telescope and instrument info
   data['instrument']   = header.get('INSTRUME', 'SDSS')
   data['telescope']    = header.get('TELESCOP', 'SDSS 2.5-M')
   data['exptime']      = np.round(header.get('EXPTIME', -1), 0)
   data['resolution']   = 1900
   data['barycor']      = header.get('HELIO_RV', -1)
   data['barycor_bool'] = True
   data['observer']     = header.get('OBSERVER', 'UK')
   data['filetype']     = 'SDSS_final'

   # observing conditions
   data['wind_speed'] = header.get('WINDS', -1)
   data['wind_direction'] = header.get('WINDD', -1)

   if 'SPEC_ID' in header:
      data['url'] = "http://skyserver.sdss.org/dr15/en/tools/quicklook/summary.aspx?sid="+header['SPEC_ID']

   return data


def derive_baches_info(header):
    """
        Read header information from an OST/BACHES spectrum
    """

    data = {}

    #   HJD
    if 'JD-HELIO' in header:
        data['hjd'] = header['JD-HELIO']
    elif 'JD' in header:
        data['hjd'] = header['JD']
    elif 'DATE-OBS' in header:
        date        = header.get('DATE-OBS', '2000-00-00')
        if 'T' not in date:
            if 'UT' in header:
                ut          = header.get('UT', '00:00:00.0')
                data['hjd'] = Time(date+'T'+ut, format='fits').jd
        else:
            data['hjd'] = Time(
                header.get('DATE-OBS', '2000-00-00T00:00:00.0Z'),
                format='fits'
                ).jd
    else:
        data['hjd'] = 2400000

    #   Pointing info
    if 'OBJCTRA' in header:
        value  = header['OBJCTRA']
        try:
            data['ra'] = Angle(value.strip(), unit='hour').degree
        except:
            data['ra'] = -1
    else:
        data['ra']  = header.get('RA', -1)

    if 'OBJCTDEC' in header:
        value = header['OBJCTDEC']
        try:
            data['dec'] = Angle(value.strip(), unit='degree').degree
        except:
            data['dec'] = -1
    else:
        data['dec'] = header.get('DEC', -1)

    data['alt'] = float(header.get('OBJCTALT', -1))
    data['az']  = float(header.get('OBJCTAZ', -1))

    #   Object
    data['objectname'] = header.get('OBJECT', '')
    if data['objectname'].strip() == '':
        data['objectname'] = header.get('FILENAME', '')

    #   Telescope and instrument info
    data['instrument']   = header.get('INSTRUME', 'SDSS')
    data['telescope']    = header.get('TELESCOP', 'SDSS 2.5-M')
    data['exptime']      = np.round(header.get('EXPTIME', -1), 0)
    data['resolution']   = 150000
    data['airmass']      = header.get('AIRMASS', -1)

    #   Observer
    data['observer']     = header.get('OBSERVER', 'UK')
    if data['observer'] == 'UK':
        data['observer'] = header.get('SWOWNER', 'UK')

    #   File characterization
    data['filetype']     = 'BACHES'

    return data


def derive_LAMOST_info(header):
   """
   Read header information from a LAMOST spectrum
   """

   data = {}

   # HJD
   data['hjd'] = Time(header.get('DATE-OBS', '2000-00-00T00:00:00.0Z'), format='fits').jd

   # pointing info
   data['objectname'] = header.get('DESIG', 'UK')

   data['ra'] = header.get('RA_OBS', -1)
   data['dec'] = header.get('DEC_OBS', -1)

   # telescope and instrument info
   data['instrument']   = header.get('INSTRUME', 'LRS')
   data['telescope']    = header.get('TELESCOP', 'LAMOST')
   data['exptime']      = np.round(header.get('EXPTIME', -1), 0)
   data['resolution']   = 1500
   data['barycor']      = header.get('HELIO_RV', -1)
   data['barycor_bool'] = True
   data['observer']     = 'UK'
   data['filetype']     = str(header.get('DATA_V', '').replace(' ', '_')) + '_' + str(header.get('ORIGIN', '')) + '_' + str(header.get('OBSID', ''))

   # observing conditions
   data['wind_speed'] = header.get('WINDS', -1)
   data['wind_direction'] = header.get('WINDD', -1)
   data['seeing'] = header.get('SEEING', -1)

   return data


def derive_MUSICOS_info(header):
   """
   Read header infromation from a MUSICOS spectrum
   (Skalnate pleso observatory of Astronomical Institute of Slovak Academy of Sciences)
   """

   data = {}

   # HJD
   data['hjd'] = header['HJD']

   # pointing info
   data['objectname'] = header.get('OBJECT', '')
   data['ra'] = Angle(header.get('RA', None), unit='hour').degree
   data['dec'] = Angle(header.get('DEC', None), unit='degree').degree

   # telescope and instrument info
   data['instrument'] = header.get('INSTRUME', 'UK')
   data['telescope'] = header.get('TELESCOP', 'UK')
   data['exptime'] = np.round(header.get('EXPTIME', -1), 0)
   data['observer'] = header.get('OBSERVER', 'UK')

   data['resolution'] = header.get('SPEC_RES', 35000.)
   data['snr'] = header.get('SNR5500A', -1)
   data['seeing'] = header.get('SEEING', -1)

   data['filetype'] = 'MUSICOS_final'

   data['normalized'] = True

   return data


def derive_TESS_info(header):
   """
   Read header information from a TESS lightcurve
   """

   data = {}

   # HJD
   # TESS uses truncated julian date with zero at JD=2457000
   data['hjd_start'] = 2457000 + header.get('TSTART', 0)
   data['hjd_end'] = 2457000 + header.get('TSTOP', 0)

   data['hjd'] = np.average([data['hjd_start'], data['hjd_end']])

   data['duration'] = Time(data['hjd_end']-data['hjd_start'], format='jd').jd * 24 # duration in hours

   # pointing info
   data['objectname'] = header.get('OBJECT', 'UK')

   data['ra'] = header.get('RA_OBJ', -1)
   data['dec'] = header.get('DEC_OBJ', -1)

   # telescope and instrument info
   data['instrument'] = header.get('INSTRUME', 'TESS Photometer')
   data['telescope'] = header.get('TELESCOP', 'TESS')
   data['exptime'] = 120
   data['cadence'] = 120
   data['passband'] = 'TESS.RED'
   data['observer'] = 'SPACE CRAFT'
   data['filetype'] = header.get('CREATOR', '').replace(' ', '_') + '_v_' + str(header.get('FILEVER', '')).strip() \
                      + '_rel_' + str(header.get('DATA_REL', '')).strip()

   return data
