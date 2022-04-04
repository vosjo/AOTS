import numpy as np
from astropy import units as u
from astropy.modeling import models, fitting
from astropy.stats import sigma_clip, mad_std
from scipy import interpolate, optimize
from specutils import Spectrum1D
from specutils.fitting import fit_generic_continuum
from specutils.spectra import SpectralRegion


def doppler_shift(wave, vrad, flux=None):
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
    wave_out = np.array(wave) * (1 + vrad / cc)
    if flux is not None:
        flux = np.interp(wave, wave_out, flux)
        return flux
    else:
        return wave_out


def rebin_core(wave, flux, binsize=2, mean=False):
    """
    Core rebinning routine: Rebins the spectrum by the given binsize.
    -> If there are remaining pixels, they are dropped

    Parameters:
    -----------
    wave            numpy.ndarray
        Wavelength data
    flux            numpy.ndarray
        Flux data
    binsize         int()
        Bin size
    mean            bool()
        Calculate mean instead of sum of the flux

    Returns:
    --------
    wave            numpy.ndarray
        Rebinned wavelength data
    flux            numpy.ndarray
        Rebinned flux
    """

    #   Reduce array length if it is not dividable by binsize
    while len(wave) % binsize != 0:
        wave = wave[0:-1]
        flux = flux[0:-1]

    #   Create the binned array
    waves = [wave[i::binsize] for i in range(0, binsize)]
    fluxes = [flux[i::binsize] for i in range(0, binsize)]

    #   Sum the flux
    if mean:
        flux = np.mean(fluxes, axis=0)
    else:
        flux = np.sum(fluxes, axis=0)

    #   Average the wavelength
    wave = np.mean(waves, axis=0)
    # wave = np.sum(waves, axis=0) / binsize

    return wave, flux


def rebin_spectrum(wave, flux, binsize=2, mean=False):
    """
    Rebinning wrapper: Distinguishes between echelle and simple slit spectra
        Special treatment of echelle spectra
        -> Rebins every order individually

    Parameters:
    -----------
    wave            numpy.ndarray or numpy.ndarray of numpy.ndarrays
        Wavelength data
    flux            numpy.ndarray or numpy.ndarray of numpy.ndarrays
        Flux data
    binsize         int()
        Bin size
    mean            bool()
        Calculate mean instead of sum of the flux

    Returns:
    --------
    wave            numpy.ndarray or numpy.ndarray of numpy.ndarrays
        Rebinned wavelength data
    flux            numpy.ndarray or numpy.ndarray of numpy.ndarrays
        Rebinned flux
    """

    #   Sanitize binsize I
    if binsize == 0 or binsize == None:
        binsize = 1

    #   Identify echelle spectra (np.ndarray of np.ndarrays)
    if isinstance(wave[0], np.ndarray):
        #   Prepare lists
        wave_list = []
        flux_list = []

        #   Loop over orders
        for i, w in enumerate(wave):
            #   Sanitize binsize II
            if len(w) / binsize < 4:
                binsize = int(len(w) / 4)

            #   Rebin
            _w, _f = rebin_core(w, flux[i], binsize=binsize, mean=mean)
            wave_list.append(_w)
            flux_list.append(_f)
        return np.array(wave_list), np.array(flux_list)
    else:
        #   Sanitize binsize III
        if len(wave) / binsize < 4:
            binsize = int(len(wave) / 4)

        return rebin_core(wave, flux, binsize=binsize, mean=mean)


def consecutive(data, stepsize=1):
    '''
    Find consecutive elements in a numpy array
    -> Idee: https://stackoverflow.com/questions/7352684/how-to-find-the-groups-of-consecutive-elements-in-a-numpy-array
    '''
    return np.split(data, np.where(np.diff(data) != stepsize)[0] + 1)


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
    p0 = 1.  # Initial guess
    norm_factor = optimize.fsolve(
        errfunc,
        p0,
        args=(flux_1, flux_2),
    )

    #   Normalize new spectrum
    return flux_2 * norm_factor


def norm_spectrum(spec, median_window=3, order=3):
    '''
    Normalize a spectrum

    Parameters:
    -----------
    spec:           specutils.Spectrum1D
        Spectrum to normalize
    median_window:  int()
        Window in Pixel used in median smoothing
    order:          int()
        Order of the polynomial used to find the continuum

    Returns:
    --------
    norm_spec:      specutils.Spectrum1D
        Normalized spectrum

    '''
    #   Regions that should not be used for continuum estimation,
    #   such as broad atmospheric absorption bands
    exclude_regions = [
        SpectralRegion(4295. * u.AA, 4315. * u.AA),
        # SpectralRegion(6860.* u.AA, 6880.* u.AA),
        SpectralRegion(6860. * u.AA, 6910. * u.AA),
        # SpectralRegion(7590.* u.AA, 7650.* u.AA),
        SpectralRegion(7590. * u.AA, 7680. * u.AA),
        SpectralRegion(9260. * u.AA, 9420. * u.AA),
        # SpectralRegion(11100.* u.AA, 11450.* u.AA),
        # SpectralRegion(13300.* u.AA, 14500.* u.AA),
    ]

    #   First estimate of the continuum
    #   -> will be two for late type stars because of the many absorption lines
    #   -> to limit execution time use simple LinearLSQFitter()
    #       -> reduces normalization accuracy
    _cont = fit_generic_continuum(
        spec,
        model=models.Chebyshev1D(order),
        fitter=fitting.LinearLSQFitter(),
        median_window=median_window,
        exclude_regions=exclude_regions,
    )(spec.spectral_axis)

    #   Normalize spectrum
    norm_spec = spec / _cont

    #   Sigma clip the normalized spectrum to rm spectral lines
    clip_flux = sigma_clip(
        norm_spec.flux,
        sigma_lower=1.25,
        sigma_upper=3.,
        axis=0,
        grow=1.,
    )

    #   Calculate mask
    mask = np.invert(clip_flux.recordmask)

    #   Make new spectrum
    spec_mask = Spectrum1D(
        spectral_axis=spec.spectral_axis[mask],
        flux=spec.flux[mask],
    )

    # Determine new continuum
    _cont = fit_generic_continuum(
        spec_mask,
        model=models.Chebyshev1D(order),
        fitter=fitting.LinearLSQFitter(),
        median_window=median_window,
        exclude_regions=exclude_regions,
    )(spec.spectral_axis)

    #   Normalize spectrum again
    norm_spec = spec / _cont

    return norm_spec, mad_std(norm_spec.flux)


def after_norm(flux_list):
    '''
    Afterburner that attempts to correct spectra (especially echelle orders)
    that are not well normalized before merging.
        -> only works if there in an overlap region
        -> assumes that there are only two spectra/orders that overlap
        -> assumes that one of the spectra is well normalized

    Parameters:
    -----------
    flux_list       List of numpy.ndarray()
        Flux of the spectra to normalize

    Returns:
    --------
    flux_list       List of numpy.ndarray()
        Normalized flux

    '''

    for i in range(1, len(flux_list)):
        #   Calculate flux difference
        f_diff = flux_list[i - 1] - flux_list[i]

        #   Check if overlap region exists
        #   -> if not do nothing
        if ~np.all(np.isnan(f_diff)):
            #   Determine where flux is negative
            lower = np.argwhere(f_diff < -0.01)

            #   Find consecutive elements -> build groups
            group_lower = consecutive(lower.flatten())

            #   Loop over groups
            for low in group_lower:
                #   Restrict to groups with more than 5 elements
                if len(low) > 5:
                    #   Check if flux of the first spectrum
                    #   is negative in this area
                    #   -> if yes replace
                    #   -> otherwise replace flux in the second spectrum
                    if np.nanmedian(flux_list[i - 1][low] - 1) < -0.1:
                        flux_list[i - 1][low] = flux_list[i][low]
                    else:
                        flux_list[i][low] = flux_list[i - 1][low]

            #   Determine where flux is positive
            higher = np.argwhere(f_diff > 0.01)

            #   Find consecutive elements -> build groups
            group_higher = consecutive(higher.flatten())

            #   Loop over groups
            for high in group_higher:
                #   Restrict to groups with more than 5 elements
                if len(high) > 5:
                    #   Check if flux of the second spectrum
                    #   is negative in this area
                    #   -> if yes replace
                    #   -> otherwise replace flux in the first spectrum
                    if np.nanmedian(flux_list[i][high] - 1) < -0.1:
                        flux_list[i][high] = flux_list[i - 1][high]
                    else:
                        flux_list[i - 1][high] = flux_list[i][high]

    return flux_list


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
        # flux_new_cut = flux_2[~np.isnan(flux_2)]

        #   Calculate range where:
        #       flux difference < 50% of maximum of the flux difference
        #       -> to find range where flux intersects
        id_f_x = np.argwhere(
            np.absolute(f_diff) / np.nanmax(np.absolute(f_diff)) <= 0.5
        )

        if len(id_f_x) == 0:
            return flux_1, flux_2

        #   Find center of id_f_x
        len_f_x = len(id_f_x)
        id_f_x = id_f_x[int(len_f_x / 2)][0]

        #   Median flux around 10% of id_f_x
        #   (plus 1 to ensure that range is not 0)
        x_len = int(len_f_x * 0.05) + 1
        flux_x = np.median(flux_1[id_f_x - x_len:id_f_x + x_len])
        if flux_x == 0.:
            flux_x = 1.

        #   Cut flux range to the overlap range
        f_diff_cut = f_diff[~np.isnan(f_diff)]
        #   First and last flux point
        f_diff_s = f_diff_cut[0]
        f_diff_e = f_diff_cut[-1]
        #   Find index of the above
        id_f_s = np.nanargmin(np.absolute(f_diff - f_diff_s))
        id_f_e = np.nanargmin(np.absolute(f_diff - f_diff_e))

        #   Calculate 3% of the length of the overlap range
        three_diff = int(len(f_diff_cut) * 0.03)
        #   Ensure that it is at least 1
        if three_diff == 0:
            three_diff = 1
        #   Median flux of the first and last 3% in terms of bins
        f_diff_s_med = np.median(f_diff_cut[0:three_diff])
        f_diff_e_med = np.median(f_diff_cut[three_diff * -1:])

        #   Check if flux difference stars negative and ends positive
        #   and is grater than 3% of the median flux
        #   -> if yes, use flux of the other in the respective area
        if f_diff_s_med / flux_x < -0.03 and f_diff_e_med / flux_x > 0.03:
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
        #   Calculate positions where flux is 0.
        ind = np.argwhere(flux[i] == 0.)

        f = interpolate.interp1d(
            np.delete(w, ind),
            np.delete(flux[i], ind),
            kind='cubic',
            bounds_error=False,
        )
        flux_new.append(f(new_wave))

        if i > 0:
            #   Do spectra "intersect"?
            #   -> merge if yes
            flux_1, flux_2 = merge_spectra_intersec(flux_new[i - 1], flux_new[i])

            #   Normalize flux of the individual spectra
            flux_new[i] = norm_two_spectra(flux_new[i - 1], flux_new[i])

    #   Merge flux and remove residuals NANS
    mflux = np.nanmedian(flux_new, axis=0)
    ind = np.argwhere(np.isnan(mflux))
    return np.delete(new_wave, ind), np.delete(mflux, ind)


def merge_norm(spec_list):
    '''
    Merge normalized spectra

    Parameters:
    -----------
    spec_list       List of specutils.Spectrum1D
        List with normalized spectra

    Returns:
    --------
    mwave           List of float()
        Common wave length scale
    mflux           List of float()
        Merged flux data

    '''
    #   Extract wavelength and flux data
    wave = []
    flux = []
    for spec in spec_list:
        wave.append(spec.spectral_axis)
        flux.append(spec.flux)

    #   Build common wave length scale
    mwave = np.sort(np.concatenate(wave))

    #   Prepare list for flux
    flux_new = []

    #   Loop over all spectra
    for i, w in enumerate(wave):
        #   Remove wavelength duplicates from the input arrays
        _u, indices = np.unique(w, return_index=True)
        w = w[indices]
        flux[i] = flux[i][indices]

        #   Interpolate flux on new wavelength grid
        f = interpolate.interp1d(
            w,
            flux[i],
            kind='cubic',
            bounds_error=False,
        )
        flux_new.append(f(mwave))

    #   Normalization afterburner
    #   -> attempts to improve normalization in the overlap regions
    flux_new = after_norm(flux_new)

    #   Merge flux
    mflux = np.nanmedian(flux_new, axis=0)

    return mwave, mflux


def norm_merge_spectra(spectra, median_window=3, order=3):
    '''
    Normalize spectra and merge them afterwards

    Parameters:
    -----------
    spectra:        List of specutils.Spectrum1D
        Spectra to normalize and merge
    median_window:  int()
        Window in Pixel used in median smoothing

    Returns:
    --------
    Normalized and merged spectrum

    '''

    #   Normalize spectra
    norm_spec = []
    for spec in spectra:
        norm_spec.append(
            norm_spectrum(
                spec,
                median_window=median_window,
                order=order
            )[0]
        )

    #   Merge spectra
    return merge_norm(norm_spec)


def rebin_phased_lightcurve(phase, flux, binsize=0.1):
    """
    rebins the lightcurve into phase bins with the given lenght.

    Returns: the center of the phase bins and average flux in that bin
    """

    s = np.where(~np.isnan(flux))
    phase, flux = phase[s], flux[s]

    bins = np.arange(0, 1, binsize)

    inds = np.digitize(phase, bins)

    times, fluxes = [], []
    for i in np.arange(1, len(bins)):
        if i in inds:
            fluxes.append(np.average(flux[inds == i]))
            times.append(bins[i] + binsize / 2.)

    return np.array(times), np.array(fluxes)
