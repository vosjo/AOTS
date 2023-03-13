import os

import numpy as np
from astropy.io import fits, ascii


def istext(filename):
    """
        Function that tries to estimate if a file is a text file or has a binary
        format.
        Taken from: https://stackoverflow.com/questions/1446549/how-to-identify-binary-and-text-files-using-python

        13/02/2020 Joris:  added catch for UnicodeDecodeError
        19/12/2021 Rainer: added mapping table -> restore functionality
    """
    try:
        #   Open file and read first 512 bytes
        # s=open(filename).read(512)
        s = open(filename).read(100000)
        # s = open(filename).read()

        #   Define text/ascii characters
        text_characters = "" \
                              .join(map(chr, range(32, 127))) + "" \
                              .join(list("\n\r\t\b"))

        #    Empty files are considered text
        if not s:
            return True

        #   Files with null bytes are likely binary
        if "\0" in s:
            return False

        #   Create mapping table with the characters to remove
        mtable = s.maketrans('', '', text_characters)

        #   Get the non-text characters
        t = s.translate(mtable)

        #   If more than 30% non-text characters, then
        #   this is considered a binary file
        if float(len(t)) / float(len(s)) > 0.30:
            return False
        return True
    except UnicodeDecodeError as e:
        print('         UnicodeDecodeError:')
        print('            -> File is probably a binary (FITS) file')
        print()
        #   Assuming that this is not a text file if it can't be decoded
        return False


def cal_wave(header, npoints):
    """
        Calculates wave length range from Header information
    """
    # dnu = float(header["CDELT1"]) if 'CDELT1' in header else header['CD1_1']
    # nu_0 = float(header["CRVAL1"]) # the first wavelength value
    # nu_n = nu_0 + (npoints-1)*dnu
    # wave = np.linspace(nu_0,nu_n,npoints)

    # if ('CTYP1' in header and 'log' in header['CTYP1']) or \
    # ('CTYPE1' in header and 'log' in header['CTYPE1']):
    # wave = np.exp(wave)

    if 'CRPIX1' in header:
        ref_pix = int(header["CRPIX1"]) - 1
    else:
        ref_pix = 0

    if "CDELT1" in header:
        dnu = float(header["CDELT1"])
    elif "CD1_1" in header:
        dnu = float(header["CD1_1"])
    else:
        raise Exception(
            'Can not find wavelength dispersion in header.'
            + ' Looked for CDELT1 and CD1_1'
        )

    nu0 = float(header["CRVAL1"]) - ref_pix * dnu
    nun = nu0 + (npoints - 1) * dnu
    wave = np.linspace(nu0, nun, npoints)

    #   Fix wavelengths for logarithmic sampling
    # if 'ctype1' in header and header['CTYPE1']=='log(wavelength)':
    # wave = np.exp(wave)
    # elif 'ctype1' in header and header['CTYPE1']=='AWAV-LOG':
    ##   PHOENIX spectra
    # wave = np.exp(wave)
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

    #   Prepare list for flux and wavelength data
    flux_list = []
    wave_list = []

    #   Read data from all extensions/orders
    for i in range(starthdu, nHDUs):
        #   Extract data
        data = hduLIST[i].data
        #   Extract header
        header = hduLIST[i].header

        #   Collapsed into one dimension
        _fl = data.flatten()
        flux_list.append(_fl)

        #   Calculate wave length range
        wave_list.append(cal_wave(header, len(_fl)))

    return wave_list, flux_list


def read_iraf_multispec(filename):
    '''
        Read echelle spectra reduced by IRAF and saved in the multispec format

        Parameter
        ---------
        filename        : `string`
            Name of the file/Path to the file to read

        Returns
        -------
        wave_list       : `list` of `numpy.ndarray`
            Wavelength data for each order

        flux            : `numpy.ndarray`
            Flux data for each order
    '''
    #   Get HDUs
    hdu_list = fits.open(filename, mode='readonly')

    #   Get Header
    header = hdu_list[0].header

    #   Get wavelength infos from WAT2_* keywords
    content = ''
    for WAT in header['WAT2_0*'].values():
        if len(WAT) >= 68:
            content += WAT
        else:
            content += WAT + ' '

    #   Extract start wavelength and wavelength increment for each order
    split_content = content.split('wtype=multispec')[1].split('spec')
    wave_list = []
    for content in split_content:
        if content != ' ':
            inner_content = content.split('=')[1].split(' ')
            len_inner_content = len(inner_content)
            wave_start = float(inner_content[4])
            wave_incre = float(inner_content[5])
            wave_points = int(inner_content[6])

            #   Calculate wavelength scale
            w = wave_start + (wave_points - 1) * wave_incre
            wave_list.append(np.linspace(wave_start, w, wave_points))


    #   Extract flux data
    flux = hdu_list[0].data

    return wave_list, flux


def read_spectrum(filename, return_header=False):
    """
        Read a standard 1D spectrum from the primary HDU of a FITS file or from
        a text file.

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
        data = ascii.read(filename, names=['wave', 'flux'])

        if return_header:
            return data['wave'], data['flux'], {}
        else:
            return data['wave'], data['flux']

    #   If not a text file open FITS file
    hduLIST = fits.open(filename, mode='readonly')

    #   Determine number of FITS extensions
    nHDUs = len(hduLIST)

    #   Distinguish between files containing individual Echelle orders
    #   and normal slit spectra -> assume that files with more than
    #   10 extensions are echelle files
    if nHDUs > 10:
        #   Check if primary HDU contains data
        #    => ignore if primary HDU is empty
        if hduLIST[0].data == None:
            hdu = 1
        else:
            hdu = 0

        #   Extract data
        wave, flux = read_echelle(filename, starthdu=hdu)

        #   Read header
        if return_header:
            header = fits.getheader(filename, hdu)
    else:
        hdu = 0
        try:
            telescope = fits.getval(filename, 'TELESCOP')
        except:
            try:
                telescope = fits.getval(filename, 'TELESCOP', ext=1)
                hdu = 1
            except Exception as e:
                print('Exception occurred in read_spectrum().')
                print('Context: Reading telescope info from Header.')
                print('Problem: ', e)

                telescope = 'UK'

        #    Read Header
        header = fits.getheader(filename, hdu)

        #   Read instrument
        instrument = header.get('INSTRUME', 'UK')

        #   Check for multispec entry in FITS Header
        iraf_multispec = header.get('WAT2_001', 'UK')

        ###
        #   Try instrument specific extractions
        #
        if iraf_multispec != 'UK':
            '''
            IRAF multispec echelle data
            '''
            wave, flux = read_iraf_multispec(filename)

        elif instrument in ['FEROS', 'UVES'] and not "CRVAL1" in header:
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
            data = fits.getdata(filename, 1)
            wave, flux = 10 ** data['loglam'], data['flux']

        elif 'LAMOST' in header.get('TELESCOP', ''):
            '''
            LAMOST spectra
            '''
            data = fits.getdata(filename)
            flux = data[0]
            wave = data[2]

        elif 'SBIG ST' in header.get('INSTRUME', ''):
            '''
            OST/BACHES data (also Echelle data, but only stored in one hdu)
            '''
            #   Get history from fits header because it contains the wavelength
            #   starting points of the individual orders
            history = header.get('HISTORY', '')

            #   Get data
            data = fits.getdata(filename)

            #   Extract start points (sps)
            k = 1
            sps = []
            for line in history:
                liste = line.split()
                if len(liste) == 0:
                    k = 1
                    continue
                if k == 0:
                    sps = sps + liste
                if k == 1:
                    if 'WSTART' not in liste[0]:
                        continue
                    else:
                        k = 0

            #   Prepare list for flux and wavelength data
            flux = []
            wave = []

            #   Wavelength increment
            dnu = float(header["CDELT1"])

            #   Loop over all orders
            for j, __fl in enumerate(data):
                #   Calculate wavelength array
                npoints = len(__fl)
                nu0 = float(sps[j])
                nun = nu0 + (npoints - 1) * dnu
                __wa = np.linspace(nu0, nun, npoints)

                #   Add flux and wavelength array to lists
                flux.append(__fl)
                wave.append(__wa)

        elif not "CRVAL1" in header:
            """
            Spectrum likely included as table data
            """
            data = fits.getdata(filename, 1)

            if instrument == 'XSHOOTER':
                wave = data['WAVE'][0] * 10.
                flux = data['FLUX'][0]
            else:
                if 'WAVE' in data.dtype.names or 'wave' in data.dtype.names:
                    wave = data['WAVE']  # eso DR3
                else:
                    wave = data['wavelength']

                if 'FLUX' in data.dtype.names or 'flux' in data.dtype.names:
                    flux = data['flux']
                else:
                    flux = data['FLUX_REDUCED']
        else:
            '''
            Try general 1D spectrum extraction
            '''
            try:
                #    MODS spectrograph
                if instrument in ['MODS1B', 'MODS1R', 'MODS2B', 'MODS2R']:
                    row = 1
                else:
                    row = 0

                wave, flux = read_1D_spectrum(filename, row=row)

            except Exception as e:
                print('Exception occurred in read_spectrum().')
                print('   Context: Reading spectra from FITS file,')
                print('            assuming a typical 1D spectrum layout')
                print('   Problem:', e)

                try:
                    flux = fits.getdata(filename)
                    wave = cal_wave(header, len(flux))

                except Exception as e:
                    print('Exception occurred in read_spectrum().')
                    print('   Context: Reading spectra from FITS file')
                    print('            No extraction method was successful')
                    print('   Problem:', e)

    if return_header:
        return wave, flux, header
    else:
        return wave, flux


def read_lightcurve(filename, return_header=False):
    '''
        Read lightcurve data
    '''

    header = fits.getheader(filename)

    data = fits.getdata(filename)

    time = data['time']
    flux = data['PDCSAP_FLUX']

    if return_header:
        return time, flux, header
    else:
        return time, flux


def get_rawfile_path(instance, filename):
    '''
        Set path to save the raw data: Add project slug as directory
    '''
    return os.path.join('raw_spectra', str(instance.project.slug), filename)


def get_specfile_path(instance, filename):
    '''
        Set path to save the spec file: Add project slug as directory
    '''
    return os.path.join('spectra', str(instance.project.slug), filename)
