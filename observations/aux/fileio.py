from astropy.io import fits

import numpy as np

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
   header = fits.getheader(filename)
   
   if header.get('instrume', '') == 'FEROS' and not "CRVAL1" in header:
      """
      FEROS phase 3 dataproduct
      """
      data = fits.getdata(filename, 1)
      wave, flux = data['wave'][0], data['flux'][0]
   
   elif 'SDSS' in header.get('telescop', ''):
      """
      SDSS spectrum
      """
      data = fits.getdata(filename, 1)
      wave, flux = 10**data['loglam'], data['flux']
   
   else:
      flux = fits.getdata(filename)
      if 'LAMOST' in header.get('TELESCOP', ''):
         flux = flux[0]
      
      #-- Make the equidistant wavelengthgrid using the Fits standard info
      #   in the header
      if 'CRPIX1' in header:
         ref_pix = int(header["CRPIX1"])-1
      else:
         ref_pix = 0
         
      if "CDELT1" in header:
         dnu = float(header["CDELT1"])
      elif "CD1_1" in header:
         dnu = float(header["CD1_1"])
      else:
         raise Exception('Can not find wavelength dispersion in header. Looked for CDELT1 and CD1_1')
         
      nu0 = float(header["CRVAL1"]) - ref_pix*dnu
      nun = nu0 + (len(flux)-1)*dnu
      wave = np.linspace(nu0,nun,len(flux))
      #-- fix wavelengths for logarithmic sampling
      if 'ctype1' in header and header['CTYPE1']=='log(wavelength)':
         wave = np.exp(wave)
      elif 'ctype1' in header and header['CTYPE1']=='AWAV-LOG':
         # for PHOENIX spectra
         wave = np.exp(wave)
      elif 'LAMOST' in header.get('TELESCOP', ''):
         # lamost uses log10 dispersion
         wave = 10**wave
   
   if return_header:
      return wave,flux,header
   else:
      return wave,flux
