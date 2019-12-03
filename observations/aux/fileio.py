from astropy.io import fits, ascii

import numpy as np

import string

def istext(filename):
   """
   Function that tries to estimate if a file is a text file or has a binary format.
   taken from here: https://stackoverflow.com/questions/1446549/how-to-identify-binary-and-text-files-using-python
   """
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

def read_1D_spectrum(filename):
   """
   Function to read a 1D spectrum,
   will return the wavelength and flux as numpy arrays.
   """
   hdu = fits.open(filename, mode='readonly')
   
   header = hdu[0].header
   data = hdu[0].data
   
   if len(hdu[0].data.shape) == 2:
      data = hdu[0].data[0]
      
   if len(hdu[0].data.shape) == 3:
      data = hdu[0].data[0][0]
      
   data = data.flatten()
   
   flux = data
   dnu = float(header["CDELT1"]) if 'CDELT1' in header else header['CD1_1']
   nu_0 = float(header["CRVAL1"]) # the first wavelength value
   nu_n = nu_0 + (len(flux)-1)*dnu 
   wave = np.linspace(nu_0,nu_n,len(flux)) 
   
   
   
   if ('CTYP1' in header and 'log' in header['CTYP1']) or \
      ('CTYPE1' in header and 'log' in header['CTYPE1']):
      wave = np.exp(wave)
   
   return wave, flux

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
   
   
   if istext(filename):
      # treat this as a text file with 2 columns containing wavelength and flux
      # text files are considered to not contain a header!
      
      data = ascii.read(filename, names = ['wave', 'flux'])
      
      if return_header:
         return data['wave'], data['flux'], {}
      else:
         return data['wave'], data['flux']
   
   print( filename )
   
   header = fits.getheader(filename)
   
   try:
      wave, flux = read_1D_spectrum(filename)
   except Exception as e:
      print (e)
      
      if header.get('instrume', '') in ['FEROS', 'UVES'] and not "CRVAL1" in header:
         """
         FEROS or UVES phase 3 dataproduct
         """
         data = fits.getdata(filename, 1)
         
         if 'FLUX' in data.dtype.names:
            flux = data['FLUX'][0]
         elif 'FLUX_REDUCED' in data.dtype.names:
            flux = data['FLUX_REDUCED'][0]
         else:
            flux = data['BGFLUX_REDUCED'][0]
         
         wave = data['wave'][0]
      
      elif not "CRVAL1" in header:
         """
         spectrum likely included as table data
         """
         
         data = fits.getdata(filename, 1)
         
         if 'WAVE' in data.dtype.names or 'wave' in data.dtype.names:
            wave = data['WAVE'] # eso DR3
         else:
            wave = data['wavelength']
         
         if 'FLUX' in data.dtype.names or 'flux' in data.dtype.names:
            flux = data['flux']
         else:
            flux = data['FLUX_REDUCED']
      
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


def read_lightcurve(filename, return_header=False):
   
   header = fits.getheader(filename)
   
   data = fits.getdata(filename)
   
   time = data['time']
   flux = data['PDCSAP_FLUX']
   
   
   if return_header:
      return time,flux,header
   else:
      return time,flux
