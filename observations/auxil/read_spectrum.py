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


###
#   RawSpecFile
#
def derive_raw_file_info(raw_file_id, return_object_properties=False):
    """
        Read some basic info from the raw file and store it in the database

        Parameters
        ----------
        raw_file_id                 : `integer`
            ID of the raw file

        return_object_properties    : `boolean`, optional
            If `True` the object name, right ascension, declination will be
            returned
            Default is ``False``

        Returns
        -------
        object_name                 : `string`, optional
            Object name

        ra                          : `float`, optional
            Right ascension in degree

        dec                         : `float`, optional
            Declination in degree
    """
    #   Initialize file and read Header
    raw_file = RawSpecFile.objects.get(pk=raw_file_id)
    header = raw_file.get_header()

    #   Extract info from Header
    data = instrument_headers.extract_header_raw(header)

    #   Set variables
    raw_file.hjd = data['hjd']
    raw_file.instrument = data['instrument']
    raw_file.filetype = data['filetype']
    raw_file.exptime = data['exptime']
    raw_file.obs_date = Time(data['hjd'], format='jd', precision=0).iso

    #   Save file
    raw_file.save()

    #   Get object name, ra, and dec if filetype is 'Science'
    if return_object_properties:
        return data['objectname'], data['ra'], data['dec']


def add_and_process_science_raw_spec(raw_file_id, create_new_star=True):
    """
        Processes raw spectrum files, attempts to identify science spectra
        (actual exposures of objects), and uses the object information and
        observation time to identify the 'Star' and the reduced 'Spec files'
        in the database to which the raw spectrum belongs.

        Parameters:
        -----------
        raw_file_id         : `integer`
            ID of the raw file

        create_new_star     : `boolean`, optional
            If `True`, a new 'Star' object will be created if an object is
            specified in the FITS header but is not yet in the database.
            Default is ``True``.

        Returns:
        --------
        is_object_addable   : `boolean`
            Is `True` is the raw spec file was successfully added, False
            otherwise.

        message             : `string`
            Contains info on what went wrong, or just a success message.

        is_object_file      : `boolean`
            Is `True` if the raw specfile is an actual exposure of an object

        spec_file_pk        : `integer`

        star_pk             : `integer`
    """
    #   Initialize return message
    message = ""

    #   Fill raw file model with infos
    object_name, ra, dec = derive_raw_file_info(
        raw_file_id,
        return_object_properties=True,
    )

    #   Initialize raw file instance and extract file name
    raw_file = RawSpecFile.objects.get(pk=raw_file_id)
    raw_file_name = raw_file.rawfile.name.split('/')[-1]

    if raw_file.filetype == 'Science' and object_name != '' and ra != 0. and dec != 0.:
        ###
        #   Check if the raw file already exists
        #
        #   TODO: Check this with respect to multiobject spectrographs.
        #         Add a switch that avoids this check?
        #         Resolve object name with Simbad to get coordinates?
        #         But object might be a cluster or so...
        other_raw_spec_files = RawSpecFile.objects \
            .exclude(id__exact=raw_file_id) \
            .filter(hjd__range=[
                raw_file.hjd - 0.00000001,
                raw_file.hjd + 0.00000001
            ]) \
            .filter(instrument__iexact=raw_file.instrument) \
            .filter(filetype__iexact=raw_file.filetype) \
            .filter(project__exact=raw_file.project.pk)

        #   If file is already in the database, use this one
        if len(other_raw_spec_files) > 0:
            #   Remove the uploaded raw file
            raw_file.delete()

            message += (f"{raw_file_name} (raw file) for object {object_name} "
                        f"is a duplicate and already exists in the database. "
                        f"Contact the database administrator if this is "
                        f"incorrect, or if you are trying to upload raw data "
                        f"from a multi-object spectrograph.")

            return False, message, True, None, None
        else:
            #   Add raw specfile to existing spec file
            spec_files = SpecFile.objects \
                .filter(project__exact=raw_file.project) \
                .filter(ra__range=[ra - 1 / 3600., ra + 1 / 3600.]) \
                .filter(dec__range=[dec - 1 / 3600., dec + 1 / 3600.]) \
                .filter(instrument__iexact=raw_file.instrument) \
                .filter(hjd__range=(raw_file.hjd - 0.001, raw_file.hjd + 0.001))

            if len(spec_files) > 0:
                #   TODO: Instead of getting the first spec file add an error message and
                #         redirect the user to the detailed raw spectrum upload method.
                spec_file = spec_files[0]
                spec_file.rawspecfile_set.add(raw_file)
                spec_file_pk = spec_file.pk
                message += (f"Raw spectrum added to existing spectrum file "
                            f"{spec_file} (Target: {spec_file.objectname})")
            else:
                spec_file_pk = None
                message += (f"No reduced spectrum found for this raw spectrum "
                            f"file: {raw_file_name} (Target: {object_name})")

            #   Add the raw spectrum to existing or new star
            star = Star.objects.filter(project__exact=raw_file.project) \
                .filter(ra__range=(ra - 0.1, ra + 0.1)) \
                .filter(dec__range=(dec - 0.1, dec + 0.1))

            if len(star) > 0:
                #     If there is one or more stars returned, select the
                #     closest star
                star = star.annotate(
                    distance=ExpressionWrapper(
                        ((F('ra') - ra) ** 2 + (F('dec') - dec) ** 2) ** (1. / 2.),
                        output_field=DecimalField()
                    )
                ).order_by('distance')[0]
                #   TODO: Instead of getting the closes star add an error message and
                #         redirect the user to the detailed raw spectrum upload method.
                star.rawspecfile_set.add(raw_file)
                message += (f", and added to existing System {star} (_r = "
                            f"{star.distance})")
            else:
                if not create_new_star:
                    raw_file.delete()
                    message += (f", no star found, raw data file "
                                f"({raw_file_name}) NOT added to database.")
                    return False, message, True, None, None

                #     Need to make a new star
                star = Star(
                    name=object_name,
                    ra=ra,
                    dec=dec,
                    project=raw_file.project,
                )
                star.save()

                star.rawspecfile_set.add(raw_file)

                message += f", and added to new System {star}"

            return True, message, True, spec_file_pk, star.pk
    else:
        return True, "", False, None, None


def process_raw_spec(rawfile_id, specfiles, stars):
    """
        Check if the file is a duplicate, and if not, add it to a specfile

        Parameters:
        -----------
        rawfile_id          : `integer`
            ID of the raw file

        specfiles           : `QuerySet`
            SpecFile instances

        stars               : `QuerySet`
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
    derive_raw_file_info(rawfile_id)

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
