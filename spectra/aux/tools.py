
import numpy as np

def doppler_shift(wave,vrad,flux=None):
    """
    Shift a spectrum with towards the red or blue side with some radial velocity.
    
    @param wave: wavelength array
    @type wave: ndarray
    @param vrad: radial velocity (negative shifts towards blue, positive towards red)
    @type vrad: float (units: km/s) or tuple (float,'units')
    @param vrad_units: units of radial velocity (default: km/s)
    @type vrad_units: str (interpretable for C{units.conversions.convert})
    @return: shifted wavelength array/shifted flux
    @rtype: ndarray
    """ 
    cc = 299792.458
    wave_out = wave * (1+vrad/cc)
    if flux is not None:
        flux = np.interp(wave,wave_out,flux)
        return flux
    else:
        return wave_out


def rebin_spectrum(wave, flux, binsize=2):
   """
   Rebins the spectrum by the given binsize. If there are remaining pixels, they are dropped
   
   Returns: the rebinned wavelength and flux
   """
   
   # reduce array length if it is not dividable by binsize
   while len(wave) % binsize != 0:
      wave = wave[0:-1]
      flux = flux[0:-1]
   
   # create the binned array
   waves = [wave[i::binsize] for i in range(0,binsize)]
   fluxes = [flux[i::binsize] for i in range(0,binsize)]
   
   # sum the flux
   flux = np.sum(fluxes, axis=0)
   
   # average the wavelength
   wave = np.sum(waves, axis=0) / binsize
   
   return wave, flux
   
