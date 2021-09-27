from astropy.io import fits, ascii

import numpy as np

from . import tools

def istext(filename):
   """
   Function that tries to estimate if a file is a text file or has a binary format.
   taken from here: https://stackoverflow.com/questions/1446549/how-to-identify-binary-and-text-files-using-python

   13/02/2020 joris: added catch for UnicodeDecodeError
   """
   try:
      s=open(filename).read(512)
      text_characters = "".join(map(chr, range(32, 127))) + "".join( list("\n\r\t\b"))
      #_null_trans = str.maketrans("", "")
      if not s:
         # Empty files are considered text
         return True
      if "\0" in s:
         # Files with null bytes are likely binary
         return False
      # Get the non-text characters (maps a character to itself then
      # use the 'remove' option to get rid of the text characters.)
      t = s.translate(text_characters)
      # If more than 30% non-text characters, then
      # this is considered a binary file
      if float(len(t))/float(len(s)) > 0.30:
         return False
      return True
   except UnicodeDecodeError:
      # assuming that this is not a text file if it can't be decoded
      return False


def cal_wave(header, npoints):
    """
    Calculates wave length range from Header information
    """
    dnu = float(header["CDELT1"]) if 'CDELT1' in header else header['CD1_1']
    nu_0 = float(header["CRVAL1"]) # the first wavelength value
    nu_n = nu_0 + (npoints-1)*dnu
    wave = np.linspace(nu_0,nu_n,npoints)

    if ('CTYP1' in header and 'log' in header['CTYP1']) or \
        ('CTYPE1' in header and 'log' in header['CTYPE1']):
        wave = np.exp(wave)

    return wave


def read_1D_spectrum(filename, row=0):
    """
    Function to read a 1D spectrum,
    will return the wavelength and flux as numpy arrays.
    """
    hdu = fits.open(filename, mode='readonly')

    header = hdu[0].header
    data = hdu[0].data

    if len(hdu[0].data.shape) == 2:
        data = hdu[0].data[row]

    if len(hdu[0].data.shape) == 3:
        data = hdu[0].data[0][row]

    flux = data.flatten()

    #   Calculate wave length range
    wave = cal_wave(header, len(flux))

    return wave, flux


def read_echelle(filename, starthdu=0):
    """
    Function to read individual orders of an echelle spectrum,
    will return the merged wavelength scale and the merged flux
    as numpy arrays.
    """

    #   Open FITS file
    hduLIST = fits.open(filename)

    #   Determine number of extensions
    nHDUs = len(hduLIST)

    #   Prepare list for flux and wave length data
    flux = []
    wave = []

    #   Read data from all extensions/orders
    for i in range(starthdu,nHDUs):
        #   Extract data
        data   = hduLIST[i].data
        #   Extract header
        header = hduLIST[i].header

        #   Collapsed into one dimension
        _fl = data.flatten()
        flux.append(_fl)

        #   Calculate wave length range
        wave.append(cal_wave(header, len(_fl)))

    #   Merge spectra
    mwave, mflux = tools.merge_spectra(wave, flux)

    return mwave, mflux


def read_spectrum(filename, return_header=False):
    """
    Read a standard 1D spectrum from the primary HDU of a FITS file.

    @param filename: FITS filename
    @type filename: str
    @param return_header: return header information as dictionary
    @type return_header: bool
    @return: wavelength, flux(, header)
    @rtype: array, array(, dict)
    """

    # Check if file is a text file
    if istext(filename):
        #   Assume that this file has 2 columns containing wavelength and flux
        #   Text files are considered to not contain a header!
        data = ascii.read(filename, names = ['wave', 'flux'])

        if return_header:
            return data['wave'], data['flux'], {}
        else:
            return data['wave'], data['flux']

    #   If not a text file open FITS file
    hduLIST = fits.open(filename, mode='readonly')

    #   Determine number of FITS extensions
    nHDUs = len(hduLIST)

    #    Check if primary Header contains information on the
    #    telescope and instrument
    #    => ignore primary Header if that is not the case
    try:
        telescope  = fits.getval(filename, 'TELESCOP')
        instrument = fits.getval(filename, 'INSTRUME')
        hdu = 0
    except:
        try:
            telescope  = fits.getval(filename, 'TELESCOP', ext=1)
            instrument = fits.getval(filename, 'INSTRUME', ext=1)
            hdu = 1
        except Exception as e:
            print(e)

    #    Read Header
    header = fits.getheader(filename, hdu)

    #   Assume that files with more than 10 extensions are echelle files
    if nHDUs > 10:
        wave, flux = read_echelle(filename, starthdu=hdu)
    else:
        #    MODS spectrograph
        if instrument in ['MODS1B', 'MODS1R', 'MODS2B', 'MODS2R']:
            row=1
        else:
            row=0

        #    Try general 1D spectrum extraction
        try:
            wave, flux = read_1D_spectrum(filename, row=row)
        except Exception as e:
            print (e)

            #     Switch to instrument specific extractions
            if instrument in ['FEROS', 'UVES'] and not "CRVAL1" in header:
                """
                FEROS or UVES (phase 3 data product)
                """
                data = fits.getdata(filename, 1)

                if 'FLUX' in data.dtype.names:
                    flux = data['FLUX'][0]
                elif 'FLUX_REDUCED' in data.dtype.names:
                    flux = data['FLUX_REDUCED'][0]
                else:
                    flux = data['BGFLUX_REDUCED'][0]

                wave = data['wave'][0]

            elif 'SDSS' in header.get('telescop', ''):
                """
                SDSS spectrum
                """
                data       = fits.getdata(filename, 1)
                wave, flux = 10**data['loglam'], data['flux']

            elif not "CRVAL1" in header:
                """
                Spectrum likely included as table data
                """
                data = fits.getdata(filename, 1)

                if instrument == 'XSHOOTER':
                    wave = data['WAVE'][0]*10.
                    flux = data['FLUX'][0]
                else:
                    if 'WAVE' in data.dtype.names or 'wave' in data.dtype.names:
                        wave = data['WAVE'] # eso DR3
                    else:
                        wave = data['wavelength']

                    if 'FLUX' in data.dtype.names or 'flux' in data.dtype.names:
                        flux = data['flux']
                    else:
                        flux = data['FLUX_REDUCED']

            else:
                flux = fits.getdata(filename)
                if 'LAMOST' in header.get('TELESCOP', ''):
                    flux = flux[0]

                #   Make the equidistant wavelength grid using the Fits standard
                #   info in the header
                if 'CRPIX1' in header:
                    ref_pix = int(header["CRPIX1"])-1
                else:
                    ref_pix = 0

                if "CDELT1" in header:
                    dnu = float(header["CDELT1"])
                elif "CD1_1" in header:
                    dnu = float(header["CD1_1"])
                else:
                    raise Exception(
                        'Can not find wavelength dispersion in header.'
                        +' Looked for CDELT1 and CD1_1'
                        )

                nu0 = float(header["CRVAL1"]) - ref_pix*dnu
                nun = nu0 + (len(flux)-1)*dnu
                wave = np.linspace(nu0,nun,len(flux))
                #   Fix wavelengths for logarithmic sampling
                if 'ctype1' in header and header['CTYPE1']=='log(wavelength)':
                    wave = np.exp(wave)
                elif 'ctype1' in header and header['CTYPE1']=='AWAV-LOG':
                    #   PHOENIX spectra
                    wave = np.exp(wave)
                elif 'LAMOST' in header.get('TELESCOP', ''):
                    #   Lamost uses log10 dispersion
                    wave = 10**wave

    if return_header:
        return wave,flux,header
    else:
        return wave,flux


def read_lightcurve(filename, return_header=False):

   header = fits.getheader(filename)

   data = fits.getdata(filename)

   time = data['time']
   flux = data['PDCSAP_FLUX']


   if return_header:
      return time,flux,header
   else:
      return time,flux
