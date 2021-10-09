
import numpy as np

from scipy import interpolate, optimize


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


def errfunc(p, a1, a2):
    """
    Function to minimize difference between spectra
    """
    #   Calculate difference
    diff = np.nansum(a1 - a2 * p)

    #   If 'diff' is 0, spectra probably have no overlap
    #   -> calculate sum of the individual spectra
    if diff == 0.:
        diff = np.nansum(a1) - np.nansum(a2) * p

    return diff


def norm_two_spectra(flux_1, flux_2):
    '''
    Normalize flux of two spectra

    Idea: https://stackoverflow.com/questions/13846213/create-composite-spectrum-from-two-unnormalized-spectra
    '''
    #   Calculate normalization factor
    p0 = 1.  #  Initial guess
    norm_factor = optimize.fsolve(
        errfunc,
        p0,
        args=(flux_1, flux_2),
        )

    #   Normalize new spectrum
    return flux_2*norm_factor


def merge_spectra_intersec(flux_1, flux_2):
    '''
    Combines two spectra whose flux intersects
    -> tries to avoid jumps
    '''

    #   Calculate flux difference
    f_diff = flux_1 - flux_2

    #   Check if overlap exists?
    if ~np.all(np.isnan(f_diff)):
        #   Cut flux range to the overlap range
        flux_new_cut = flux_2[~np.isnan(flux_2)]

        #   Calculate first 5% of the flux range
        first_flux   = int(len(flux_new_cut)*0.05)+1

        #   Calculate median of the first 5%
        med_flux_new = np.median(flux_new_cut[0:first_flux])

        #   Calculate range where range flux < 0.8 * med_flux_new
        #   -> to find range where flux intersect
        id_f_x = np.argwhere(np.absolute(f_diff)/med_flux_new < 0.8)

        #   Find center of id_f_x
        len_f_x = len(id_f_x)
        id_f_x = id_f_x[int(len_f_x/2)][0]

        #   Median flux around 10% of id_f_x
        #   (plus 1 to ensure that range is not 0)
        x_len = int(len_f_x*0.05)+1
        flux_x = np.median(flux_1[id_f_x-x_len:id_f_x+x_len])

        #   Cut flux range to the overlap range
        f_diff_cut = f_diff[~np.isnan(f_diff)]
        #   First and last flux point
        f_diff_s   = f_diff_cut[0]
        f_diff_e   = f_diff_cut[-1]
        #   Find index of the above
        id_f_s     = np.nanargmin(np.absolute(f_diff-f_diff_s))
        id_f_e     = np.nanargmin(np.absolute(f_diff-f_diff_e))

        #   Calculate 3% of the length of the overlap range
        three_diff = int(len(f_diff_cut)*0.03)
        #   Ensure that it is at least 1
        if three_diff == 0:
            three_diff = 1
        #   Median flux of the first and last 3% in terms of bins
        f_diff_s_med = np.median(f_diff_cut[0:three_diff])
        f_diff_e_med = np.median(f_diff_cut[three_diff*-1:])

        #   Check if flux difference stars negative and ends positive
        #   and is grater than 3% of the median flux
        #   -> if yes, use flux of the other in the respective area
        if f_diff_s_med/flux_x < -0.03 and f_diff_e_med/flux_x > 0.03:
            flux_2[id_f_s:id_f_x] = flux_1[id_f_s:id_f_x]
            flux_1[id_f_x:id_f_e] = flux_2[id_f_x:id_f_e]

    return flux_1, flux_2


def merge_spectra(wave, flux):
    """
    Merge spectra

    Returns: the resampled wavelength scale and the merged flux
    """

    #   Build common wave length scale
    new_wave = np.sort(np.concatenate(wave))

    #   Prepare list for flux
    flux_new = []

    #   Loop over all spectra
    for i, w in enumerate(wave):
        f = interpolate.interp1d(
            w,
            flux[i],
            kind='cubic',
            bounds_error=False
            )
        flux_new.append(f(new_wave))

        if i>0:
            #   Do spectra "intersect"?
            #   -> merge if yes
            flux_1, flux_2 = merge_spectra_intersec(flux_new[i-1], flux_new[i])

            # Normalize flux of the individual spectra
            flux_new[i] = norm_two_spectra(flux_new[i-1], flux_new[i])

    #   Merge flux
    mflux  = np.nanmedian(flux_new, axis=0)

    return new_wave, mflux


def rebin_phased_lightcurve(phase, flux, binsize=0.1):
   """
   rebins the lightcurve into phase bins with the given lenght.

   Returns: the center of the phase bins and average flux in that bin
   """

   s = np.where(~np.isnan(flux))
   phase, flux = phase[s], flux[s]

   bins = np.arange(0,1,binsize)

   inds = np.digitize(phase,bins)

   times, fluxes = [], []
   for i in np.arange(1,len(bins)):
      if i in inds:
         fluxes.append(np.average(flux[inds==i]))
         times.append(bins[i]+binsize/2.)

   return np.array(times), np.array(fluxes)

