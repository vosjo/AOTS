import astropy.units as u
import numpy as np
from astroplan.moon import moon_illumination
from astropy.coordinates import SkyCoord, AltAz, get_moon
from astropy.time import Time
from django.db.models import F, ExpressionWrapper, DecimalField

from observations.models import (
    Spectrum,
    UserInfo,
    SpecFile,
    RawSpecFile,
    Observatory,
)
from stars.models import Star
from . import instrument_headers


###############################################################################

def get_wind_direction(degrees):
    """
        Converts degrees to a direction
    """
    if degrees < 0 or degrees > 360:
        return 'NA'
    if degrees > 337.5 or degrees < 22.5:
        return 'N'
    elif degrees < 67.5:
        return 'NE'
    elif degrees < 112.5:
        return 'E'
    elif degrees < 157.5:
        return 'SE'
    elif degrees < 202.5:
        return 'S'
    elif degrees < 247.5:
        return 'SW'
    elif degrees < 292.5:
        return 'W'
    else:
        return 'NW'


def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


###    Spectrum    ###

def derive_spectrum_info(spectrum_pk, user_info={}):
    """
        Function to derive extra information about the observations from the
        fits files, calculate several parameters, and derive weather information
        from external sources if possible.

        This information is stored in the spectrum database entry
    """
    #   Get spectrum
    spectrum = Spectrum.objects.get(pk=spectrum_pk)
    wave, flux, header = spectrum.get_spectrum()

    #   Get min and max wavelength
    spectrum.minwave = np.min(np.array(wave).flatten())
    spectrum.maxwave = np.max(np.array(wave).flatten())

    #   Load info from spectrum header
    data = instrument_headers.extract_header_info(header, user_info=user_info)

    #   HJD
    spectrum.hjd = data.get('hjd', 2400000)

    #   Pointing info
    # spectrum.objectname = data.get('objectname', '')
    spectrum.objectname = data.get('objectname', spectrum.hjd)
    spectrum.ra = data.get('ra', -1)
    spectrum.dec = data.get('dec', -1)
    spectrum.alt = data.get('alt', -1)
    spectrum.az = data.get('az', -1)
    spectrum.airmass = data.get('airmass', -1)

    # telescope and instrument info
    spectrum.instrument = data.get('instrument', 'UK')
    spectrum.telescope = data.get('telescope', 'UK')
    spectrum.exptime = data.get('exptime', -1)
    spectrum.observer = data.get('observer', 'UK')
    spectrum.resolution = data.get('resolution', -1)
    spectrum.snr = data.get('snr', -1)
    spectrum.barycor = data.get('barycor', 0)
    spectrum.barycor_bool = data.get('barycor_bool', False)

    #    Spectrum normalized?
    spectrum.normalized = data.get('normalized', False)

    #    Master spectrum or decomposed spectrum?
    spectrum.master = data.get('master', False)
    spectrum.decomposed = data.get('decomposed', False)

    #   Observing conditions
    if isfloat(data.get('wind_speed', -1)):
        spectrum.wind_speed = data.get('wind_speed', -1)

    if isfloat(data.get('wind_direction', -1)):
        spectrum.wind_direction = data.get('wind_direction', -1)

    spectrum.seeing = data.get('seeing', -1)

    #    Flux unit & calibrated flux?
    spectrum.fluxcal = data.get('fluxcal', False)
    spectrum.flux_units = data.get('flux_units', 'arbitrary unit')

    if spectrum.fluxcal:
        spectrum.flux_units = data.get('flux_units', 'ergs/cm/cm/s/A')

    if spectrum.normalized:
        spectrum.flux_units = 'normalized'
        spectrum.fluxcal = False

    #    Note
    spectrum.note = data.get('note', '')

    #    Observatory
    if 'obs_pk' in user_info.keys():
        #   Selection from dropdown in the user info form
        spectrum.observatory = Observatory.objects.get(pk=user_info['obs_pk'])
    elif 'observatory_id' in user_info.keys():
        #   Selection based on the information given in the user info form
        if user_info['observatory_id'] == None:
            #   If form contains no information try header
            spectrum.observatory = instrument_headers.get_observatory(
                header,
                spectrum.project,
            )
        else:
            spectrum.observatory = Observatory.objects.get(
                pk=user_info['observatory_id']
            )
    else:
        #   Extract observatory infos from header or create a new observatory
        spectrum.observatory = instrument_headers.get_observatory(
            header,
            spectrum.project,
        )

    #   Save the changes
    spectrum.save()

    #   Calculate moon parameters
    time = Time(spectrum.hjd, format='jd')

    #   Moon illumination wit astroplan (astroplan returns a fraction, but we
    #   store percentage)
    spectrum.moon_illumination = np.round(moon_illumination(time=time) * 100, 1)

    #   Get the sky and moon coordinates at time and location of observations
    sky = SkyCoord(ra=spectrum.ra * u.deg, dec=spectrum.dec * u.deg, )
    moon = get_moon(time)

    #   Set observatory and transform sky coordinates to altitude & azimuth
    observatory = spectrum.observatory.get_EarthLocation()
    frame = AltAz(obstime=time, location=observatory)

    star = sky.transform_to(frame)
    moon = moon.transform_to(frame)

    #   Store the separation between moon and target
    spectrum.moon_separation = np.round(star.separation(moon).degree, 1)

    #   Get object alt-az and airmass if not stored in header
    if spectrum.alt <= 0:
        spectrum.alt = star.alt.degree
    if spectrum.az <= 0:
        spectrum.az = star.az.degree
    if spectrum.airmass <= 0:
        spectrum.airmass = np.round(star.secz.value, 2)

    #   Barycentric correction
    if not spectrum.barycor_bool:
        vb = sky.radial_velocity_correction(
            obstime=time,
            location=observatory,
        )
        vb = vb.to(u.km / u.s)
        spectrum.barycor = vb.value

    #   Save the changes
    spectrum.save()

    return "Spectrum details added/updated", True


###     Specfile    ###

def derive_specfile_info(specfile_id, user_info={}):
    """
        Read some basic info from the spectrum and store it in the database
    """
    #   Initialize file
    specfile = SpecFile.objects.get(pk=specfile_id)

    #   Read Data & Header
    wave, flux, h = specfile.get_spectrum()

    #   Extract info from Header
    data = instrument_headers.extract_header_info(h, user_info=user_info)

    #   Set variables
    specfile.hjd = data.get('hjd', 2400000)
    specfile.instrument = data.get('instrument', 'UK')
    specfile.filetype = data.get('filetype', 'UK')
    specfile.ra = data.get('ra', -1)
    specfile.dec = data.get('dec', -1)
    specfile.obs_date = Time(data['hjd'], format='jd', precision=0).iso
    specfile.exptime = data.get('exptime', -1)
    specfile.resolution = data.get('resolution', -1)
    specfile.snr = data.get('snr', -1)

    #   Save file
    specfile.save()

    return "File details added/updated", True


def process_specfile(specfile_id, create_new_star=True,
                     add_to_existing_spectrum=True, user_info={}):
    """
        Check if the specfile is a duplicate, and if not, add it to a spectrum
        and target star.

        returns success, message
        success is True is the specfile was successfully added, False otherwise.
        the message contains info on what went wrong, or just a success message

        If user_info is provided, this will overwrite the data extracted from
        the header, if a header is present.
    """
    message = ""

    derive_specfile_info(specfile_id, user_info=user_info)

    specfile = SpecFile.objects.get(pk=specfile_id)

    # -- check for duplicates
    duplicates = SpecFile.objects.exclude(id__exact=specfile_id) \
        .filter(ra__range=[specfile.ra - 1 / 3600., specfile.ra + 1 / 3600.]) \
        .filter(dec__range=[specfile.dec - 1 / 3600., specfile.dec + 1 / 3600.]) \
        .filter(hjd__range=[specfile.hjd - 0.00000001, specfile.hjd + 0.00000001]) \
        .filter(instrument__iexact=specfile.instrument) \
        .filter(filetype__iexact=specfile.filetype) \
        .filter(project__exact=specfile.project.pk)

    if len(duplicates) > 0:
        #     This specfile already exists, so remove it
        specfile.delete()
        return False, "This specfile is a duplicate and was not added!"

    # -- add specfile to existing or new spectrum
    spectrum = Spectrum.objects.filter(project__exact=specfile.project) \
        .filter(ra__range=[specfile.ra - 1 / 3600., specfile.ra + 1 / 3600.]) \
        .filter(dec__range=[specfile.dec - 1 / 3600., specfile.dec + 1 / 3600.]) \
        .filter(instrument__iexact=specfile.instrument) \
        .filter(hjd__range=(specfile.hjd - 0.001, specfile.hjd + 0.001))

    if len(spectrum) > 0 and add_to_existing_spectrum:
        spectrum = spectrum[0]
        spectrum.specfile_set.add(specfile)
        message += "Specfile added to existing Spectrum {} (Target: {})" \
            .format(spectrum, spectrum.objectname)
        return True, message
    else:
        spectrum = Spectrum(project=specfile.project)
        spectrum.save()
        spectrum.specfile_set.add(specfile)

        #     Load extra information for the spectrum
        derive_spectrum_info(
            spectrum.id,
            user_info=user_info,
        )
        spectrum.refresh_from_db()  # spectrum is not updated automatically!
        message += "Specfile added to new Spectrum {} (Target: {})" \
            .format(spectrum, spectrum.objectname)

    # -- add the spectrum to existing or new star if the spectrum is newly created
    star = Star.objects.filter(project__exact=spectrum.project) \
        .filter(ra__range=(spectrum.ra - 0.1, spectrum.ra + 0.1)) \
        .filter(dec__range=(spectrum.dec - 0.1, spectrum.dec + 0.1))

    if len(star) > 0:
        #     If there is one or more stars returned, select the closest star
        star = star.annotate(
            distance=ExpressionWrapper(
                ((F('ra') - spectrum.ra) ** 2 +
                 (F('dec') - spectrum.dec) ** 2
                 ) ** (1. / 2.),
                output_field=DecimalField()
            )
        ).order_by('distance')[0]
        star.spectrum_set.add(spectrum)
        message += ", and added to existing System {} (_r = {})".format(
            star,
            star.distance
        )
        return True, message
    else:

        if not create_new_star:
            specfile.delete()
            message += ", no star found, spectrum NOT added to database."
            return False, message

        #     Need to make a new star
        star = Star(
            name=spectrum.objectname,
            ra=spectrum.ra,
            dec=spectrum.dec,
            project=spectrum.project,
        )
        if 'classification' in user_info.keys():
            star.classification = user_info['classification']
        if 'classification_type' in user_info.keys():
            star.classification_type = user_info['classification_type']
        star.save()

        star.spectrum_set.add(spectrum)

        message += ", and added to new System {}".format(star)
        return True, message


###     RawSpecFile     ###

def derive_rawfile_info(rawfile_id, user_info={}):
    """
        Read some basic info from the raw file and store it in the database
    """

    #   Initialize file and read Header
    rawfile = RawSpecFile.objects.get(pk=rawfile_id)
    header = rawfile.get_header()

    #   Extract info from Header
    data = instrument_headers.extract_header_raw(header, user_info=user_info)

    #   Set variables
    rawfile.hjd = data['hjd']
    rawfile.instrument = data['instrument']
    rawfile.filetype = data['filetype']
    rawfile.exptime = data['exptime']
    # rawfile.obs_date   = data['date-obs']
    rawfile.obs_date = Time(data['hjd'], format='jd', precision=0).iso

    #   Save file
    rawfile.save()

    return "Raw file details added/updated", True


def process_raw_spec(rawfile_id, specfiles, stars):
    """
        Check if the file is a duplicate, and if not, add it to a specfile

        Parameters:
        -----------
        rawfile_id          : `integer`
            ID of the raw file

        specfiles           : `QuerySet
            SpecFile instances

        stars               : `QuerySet
            Star instances

        Returns:
        --------
        success             : `boolean`
            Is True is the specfile was successfully added, False otherwise.

        message             : `string`
            Contains info on what went wrong, or just a success message.
    """

    #   Initialize return message
    message = ""

    if len(specfiles) == 0 and len(stars) == 0:
        #   Check if either specfiles or stars were specified
        message = " Neither star nor spectrum specified." \
                  + " One of these is required."

        return False, message

    #   Fill rawfile model with infos
    derive_rawfile_info(rawfile_id)

    #   Initialize raw file instance and extract file name
    rawfile = RawSpecFile.objects.get(pk=rawfile_id)
    rawfilename = rawfile.rawfile.name.split('/')[-1]

    ###
    #   Check for specfile duplicates
    #
    if len(specfiles) > 0:
        #   Initialize boolean to check if raw files needs to be deleted
        rm_raw = True

        #   Loop over all spec files
        for spfile in specfiles:
            duplicates = RawSpecFile.objects.exclude(id__exact=rawfile_id) \
                .filter(hjd__range=[rawfile.hjd - 0.00000001, rawfile.hjd + 0.00000001]) \
                .filter(instrument__iexact=rawfile.instrument) \
                .filter(filetype__iexact=rawfile.filetype) \
                .filter(specfile__exact=spfile.pk) \
                .filter(project__exact=rawfile.project.pk)

            if len(duplicates) == 0:
                #   If it is not a duplicate assign raw file to Specfile
                spfile.rawspecfile_set.add(rawfile)

                #   Set "delete boolean" fo False
                rm_raw *= False

        #   Delete the raw file if duplicates exists
        if rm_raw:
            rawfile.delete()

            message = rawfilename + " (raw file) is a duplicate and was not added"

            return False, message

    ###
    #   Check for star duplicates
    #
    if len(stars) > 0:
        #   Initialize boolean to check if raw files needs to be deleted
        rm_raw = True

        #   Loop over all stars
        for star in stars:
            duplicates = RawSpecFile.objects.exclude(id__exact=rawfile_id) \
                .filter(hjd__range=[rawfile.hjd - 0.00000001, rawfile.hjd + 0.00000001]) \
                .filter(instrument__iexact=rawfile.instrument) \
                .filter(filetype__iexact=rawfile.filetype) \
                .filter(star__exact=star.pk) \
                .filter(project__exact=rawfile.project.pk)

            if len(duplicates) == 0:
                #   If it is not a duplicate assign raw file to Star
                star.rawspecfile_set.add(rawfile)

                #   Set "delete boolean" fo False
                rm_raw *= False

        #   Delete the raw file if duplicates exists
        if rm_raw:
            rawfile.delete()

            message = rawfilename + " (raw file) is a already associated with a "
            message += "star. Duplicate and was not added. Use `Change file"
            message += "allocation` option instead."

            return False, message

    ###
    #   Check if the raw file already exists
    #
    otherRawSpecFiles = RawSpecFile.objects.exclude(id__exact=rawfile_id) \
        .filter(hjd__range=[rawfile.hjd - 0.00000001, rawfile.hjd + 0.00000001]) \
        .filter(instrument__iexact=rawfile.instrument) \
        .filter(filetype__iexact=rawfile.filetype) \
        .filter(project__exact=rawfile.project.pk)

    #   If file is already in the database, use this one
    if len(otherRawSpecFiles) > 0:
        #   Use the first entry
        otherRawSpecFile = otherRawSpecFiles[0]
        otherRawSpecFileName = otherRawSpecFile.rawfile.name.split('/')[-1]

        #   Check if the existing raw spec file is already associated with a
        #   specfile
        if len(otherRawSpecFile.specfile.all()) > 0:
            SpecFileName = otherRawSpecFile.specfile.all()[0] \
                .specfile.name.split('/')[-1]
        else:
            SpecFileName = None

        #   Loop over all spec files
        for spfile in specfiles:
            #   Add raw file from the database to SpecFile
            spfile.rawspecfile_set.add(otherRawSpecFile)

        #   Loop over all stars
        for star in stars:
            #   Add raw file from the database to SpecFile
            star.rawspecfile_set.add(otherRawSpecFile)

        #   Remove the uploaded raw file
        rawfile.delete()

        if SpecFileName == None:
            message += rawfilename + " (raw file) is a duplicate. Used the " \
                       + "already uploaded file {}.".format(otherRawSpecFileName)
        else:
            message += rawfilename + " (raw file) is a duplicate and already " \
                       + "associated with the reduced file " + SpecFileName \
                       + ". Used the already uploaded file."
        return True, message

    ###
    #   Add raw file to existing specfile
    #
    message += "{} (raw file) added to:\n".format(rawfilename)
    for spfile in specfiles:
        message += "{} ({}), ".format(
            spfile,
            spfile.spectrum.star.name,
        )
    for star in stars:
        message += "{}, ".format(
            star.name,
        )
    return True, message


###     UserInfo     ###

def check_form(data_dict):
    '''
        Check that entries in 'data_dict' are not None or empty.
        Add to 'user_info' if that is the case.
    '''
    #   Prepare dictionary for provided infos
    user_info = {}

    #   Loop over entries
    for key, value in data_dict.items():
        #   Check and add
        if value != None and value != '':
            user_info[key] = value

    return user_info


def add_userinfo(user_info_dict, spectrum_pk):
    '''
        Add user infos to UserInfo model
    '''
    #   Get Spectrum
    spectrum = Spectrum.objects.get(pk=spectrum_pk)

    #   Get new UserInfo model
    info_model = UserInfo(project=spectrum.project)

    #   Fill model
    for key, value in user_info_dict.items():
        setattr(info_model, key, value)

    #   Save changes
    info_model.save()

    #   Check if Spectrum is already associated with a UserInfo instance
    user_infos = spectrum.userinfo_set.all()

    #   Check and set UserInfo
    if len(user_infos) > 0:
        info_model.delete()
        message = 'Provided information not added. Spectrum '
        message += '({}, {}) is already associated with user information' \
            .format(spectrum, spectrum.objectname)
        success = False
    else:
        spectrum.userinfo_set.add(info_model)
        message = 'Provided information added to spectrum: {} (Target: {})' \
            .format(spectrum, spectrum.objectname)
        success = True

    return success, message
