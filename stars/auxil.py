from astroquery.vizier import Vizier
from astroquery.simbad import Simbad
from astropy.coordinates import SkyCoord
from astropy.coordinates.angles import Angle

import astropy.units as u

import numpy as np

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import reverse

from .models import Star
from analysis.models import DataSource

def invalid_form(request, redirect, project_slug):
    '''
        Handel invalid forms
    '''
    #   Add message
    messages.add_message(
        request,
        messages.ERROR,
        "Invalid form. Please try again.",
        )

    #   Return and redirect
    return HttpResponseRedirect(
        reverse(redirect, kwargs={'project':project_slug})
        )
    print("Invalid form...")


def populate_system(star, star_pk):
    '''
        Analyse provided 'star' dictionary and create a Star object
    '''
    if 'get_simbad' in star:
        if star['get_simbad']:
            check_vizier = True
        else:
            check_vizier = False
    else:
        check_vizier = False

    #   Load system/star model
    sobj = Star.objects.get(pk=star_pk)

    #   Set project
    project = sobj.project

    #   Coordinates
    if check_vizier:
        customSimbad = Simbad()
        customSimbad.add_votable_fields('sptype')
        simbad_tbl = customSimbad.query_object(star["main_id"])
        if simbad_tbl is None:
            return False, "System ({}) not known by Simbad".format(
                star["main_id"]
                )
        ra  = Angle(simbad_tbl[0]['RA'].strip(), unit='hour').degree
        dec = Angle(simbad_tbl[0]['DEC'].strip(), unit='degree').degree
    else:
        ra  = float(star['ra'])
        dec = float(star['dec'])

    #   Set RA & DEC
    sobj.ra  = ra
    sobj.dec = dec

    #   Check for duplicates
    duplicates = Star.objects.filter(name=star["main_id"]) \
        .filter(ra__range=[ra - 1 / 3600., ra + 1 / 3600.]) \
        .filter(dec__range=[dec - 1 / 3600., dec + 1 / 3600.]) \
        .filter(project__exact=project.pk)

    if len(duplicates) != 0:
        return False, "System exists already: {}".format(star["main_id"])

    #   Set spectral type
    if check_vizier:
        sobj.classification  = simbad_tbl[0]['SP_TYPE']
        if simbad_tbl[0]['SP_TYPE'] != '':
            sobj.classification_type = 'SP'
    else:
        sobj.classification  = star['sp_type']
        if 'classification_type' in star:
            sobj.classification_type = star['classification_type']


    #   Set identifier
    ident = sobj.identifier_set.all()[0]
    ident.href = "http://simbad.u-strasbg.fr/simbad/" \
                 + "sim-id?Ident=" + star['main_id'] \
                     .replace(" ", "").replace('+', "%2B")
    ident.save()

    #   Add JNAME as identifier if provided
    if 'JNAME' in star:
        sobj.identifier_set.create(name=star['JNAME'])

    #   Add default Simbad name if query occurred
    #   and if it is different compared to the provided name
    if check_vizier:
        if star["main_id"].strip() != simbad_tbl[0]['MAIN_ID'].strip():
            sobj.identifier_set.create(
                name = simbad_tbl[0]['MAIN_ID'],
                href = "http://simbad.u-strasbg.fr/simbad/" \
                    + "sim-id?Ident=" + simbad_tbl[0]['MAIN_ID'] \
                        .replace(" ", "").replace('+', "%2B"),
                    )

    # -- Add Tags
    if 'tags' in star:
        for tag in star["tags"]:
            sobj.tags.add(tag)

    #-- Add photometry
    #   'simbad_id':    ID of the catalog
    #   'columns':      filter definition used by the catalog
    #   'err_columns':  filter errors used by the catalog
    #   'passbands':    internal names for the filters
    #   'photnames':    external names (e.g., in .csv files) for the filters
    #   'errs':         external names (e.g., in .csv files) for the errors
    catalogs = {
        'GAIA2': {
            'simbad_id':'I/345/gaia2',
            'columns':['Gmag', 'BPmag', 'RPmag'],
            'err_columns':['e_Gmag', 'e_BPmag', 'e_RPmag'],
            'passbands':['GAIA2.G', 'GAIA2.BP', 'GAIA2.RP'],
            'photnames':[
                'phot_g_mean_mag',
                'phot_bp_mean_mag',
                'phot_rp_mean_mag',
                ],
            'errs':[
                'phot_g_mean_magerr',
                'phot_bp_mean_magerr',
                'phot_rp_mean_magerr',
                ],
            },
        '2MASS': {
            'simbad_id':'II/246/out',
            'columns':['Jmag', 'Hmag', 'Kmag'],
            'err_columns':['e_Jmag', 'e_Hmag', 'e_Kmag'],
            'passbands':['2MASS.J', '2MASS.H', '2MASS.K'],
            'photnames':['Jmag', 'Hmag', 'Kmag'],
            'errs':['Jmagerr', 'Hmagerr', 'Kmagerr'],
            },
        'WISE': {
            'simbad_id':'II/328/allwise',
            'columns':['W1mag', 'W2mag', 'W3mag', 'W4mag'],
            'err_columns':['e_W1mag', 'e_W2mag', 'e_W3mag', 'e_W4mag'],
            'passbands':['WISE.W1', 'WISE.W2', 'WISE.W3', 'WISE.W4'],
            'photnames':['W1mag', 'W2mag', 'W3mag', 'W4mag'],
            'errs':['W1magerr', 'W2magerr', 'W3magerr', 'W4magerr'],
            },
        'GALEX': {
            'simbad_id':'II/312/ais',
            'columns':['FUV', 'NUV'],
            'err_columns':['e_FUV', 'e_NUV'],
            'passbands':['GALEX.FUV', 'GALEX.NUV'],
            'photnames':['FUV', 'NUV'],
            'errs':['FUVerr', 'NUVerr'],
            },
        'SKYMAP': {
            'simbad_id':'V/145/sky2kv5',
            'columns':['Umag', 'Vmag'],
            'err_columns':['e_Umag', 'e_Vmag'],
            'passbands':['SKYMAP.U', 'SKYMAP.V'],
            'photnames':['Umag', 'Vmag'],
            'errs':['Umagerr', 'Vmagerr'],
            },
        'APASS': {
            'simbad_id':'II/336/apass9',
            'columns':["Bmag", "Vmag", "g'mag", "r'mag", "i'mag"],
            'err_columns':["e_Bmag", "e_Vmag", "e_g'mag", "e_r'mag", "e_i'mag"],
            'passbands':['APASS.B', 'APASS.V', 'APASS.G', 'APASS.R', 'APASS.I'],
            'photnames':['APBmag', 'APVmag', 'APGmag', 'APRmag', 'APImag'],
            'errs':[
                'APBmagerr',
                'APVmagerr',
                'APGmagerr',
                'APRmagerr',
                'APImagerr',
                ],
            },
        'SDSS': {
            'simbad_id':'V/147/sdss12',
            'columns':['umag', 'gmag', 'rmag', 'imag', 'zmag'],
            'err_columns':['e_umag', 'e_gmag', 'e_rmag', 'e_imag', 'e_zmag'],
            'passbands':['SDSS.U', 'SDSS.G', 'SDSS.R', 'SDSS.I', 'SDSS.Z'],
            'photnames':[
                'SDSSUmag',
                'SDSSGmag',
                'SDSSRmag',
                'SDSSImag',
                'SDSSZmag',
                ],
            'errs':[
                'SDSSUmagerr',
                'SDSSGmagerr',
                'SDSSRmagerr',
                'SDSSImagerr',
                'SDSSZmagerr',
                ],
            },
        'PANSTAR': {
            'simbad_id':'II/349/ps1',
            'columns':['gmag', 'rmag', 'imag', 'zmag', 'ymag'],
            'err_columns':['e_gmag', 'e_rmag', 'e_imag', 'e_zmag', 'e_ymag'],
            'passbands':[
                'PANSTAR.G',
                'PANSTAR.R',
                'PANSTAR.I',
                'PANSTAR.Z',
                'PANSTAR.Y',
                ],
            'photnames':['PANGmag', 'PANRmag', 'PANImag', 'PANZmag', 'PANYmag'],
            'errs':[
                'PANGmagerr',
                'PANRmagerr',
                'PANImagerr',
                'PANZmagerr',
                'PANYmagerr',
                ],
            },
        }

    #   Loop over catalogs
    for name, content in catalogs.items():
        #   Check if photometry shall be loaded from Vizier
        if check_vizier:
            #   Define catalog and columns
            v = Vizier(
                catalog=content['simbad_id'],
                columns=content['columns']+content['err_columns'],
                )
            #   Get data, assume a radius of 1"
            photo = v.query_region(
                SkyCoord(ra=ra, dec=dec, unit=(u.deg, u.deg), frame='icrs'),
                radius=1*u.arcsec,
                )
            #   Check if catalog contains data for this object
            if len(photo) != 0:
                #   Loop over photometry bands
                for i, band in enumerate(content['columns']):
                    #   Sanitize band/filter names
                    band = band.replace("'",'_')
                    #   Get magnitudes
                    mag = photo[0][band][0]
                    #      Sanitize error names
                    err_band = content['err_columns'][i].replace("'",'_')
                    #   Get errors
                    err = photo[0][err_band][0]
                    #   Set error to zero, if it is undefined
                    if str(err) == '--' or np.isnan(err):
                        err = 0.
                    #   Check if magnitude value is valid
                    if mag != '--' and ~np.isnan(mag):
                        #   Set magnitude value and error
                        sobj.photometry_set.create(
                            band=content['passbands'][i],
                            measurement=mag,
                            error=err,
                            unit='mag',
                        )

        else:
            for i, phot in enumerate(content['photnames']):
                #   Check if photometry was provided
                if phot in star:
                    err_name = content['errs'][i]
                    #   Check if error was provided
                    if err_name in star:
                        #   Check if photometry and error is not empty
                        if (star[phot] != None and star[phot] != "" and
                            star[err_name] != None and star[err_name] != ""):
                            sobj.photometry_set.create(
                                band=content['passbands'][i],
                                measurement=star[phot],
                                error=star[err_name],
                                unit='mag',
                            )
                        #   If error is empty set it to zero
                        elif star[phot] != None and star[phot] != "":
                            sobj.photometry_set.create(
                                band=content['passbands'][i],
                                measurement=star[phot],
                                error=0.,
                                unit='mag',
                            )
                    else:
                        #   If error is not provided set it to zero
                        if star[phot] != None and star[phot] != "":
                            sobj.photometry_set.create(
                                band=content['passbands'][i],
                                measurement=star[phot],
                                error=0.,
                                unit='mag',
                            )

    if check_vizier:
        #   Download GAIA EDR3 data
        gaia_data = Vizier(
            catalog='I/350/gaiaedr3',
            columns=['Plx', 'e_Plx', 'pmRA', 'e_pmRA', 'pmDE', 'e_pmDE'],
            ).query_region(star["main_id"], radius=1*u.arcsec)

        #   Check if GAIA data is available for the source
        if len(gaia_data) != 0:
            #   Set data source
            try:
                dsgaia = DataSource.objects.get(
                    name__exact='Gaia EDR3',
                    project=project,
                )
            except DataSource.DoesNotExist:
                dsgaia = DataSource.objects.create(
                    name='Gaia EDR3',
                    note='Early 3nd Gaia data release',
                    reference='https://doi.org/10.1051/0004-6361/202141135',
                    project=project,
                )

            #   Set parallax
            if (str(gaia_data[0]['Plx']) != '--' and
                str(gaia_data[0]['e_Plx']) != '--'):
                sobj.parameter_set.create(
                    data_source=dsgaia,
                    name='parallax',
                    component=0,
                    value=gaia_data[0]['Plx'],
                    error=gaia_data[0]['e_Plx'],
                    unit='',
                )

            #   RA proper motion
            if (str(gaia_data[0]['pmRA']) != '--' and
                str(gaia_data[0]['e_pmRA']) != '--'):
                sobj.parameter_set.create(
                    data_source=dsgaia,
                    name='pmra',
                    component=0,
                    value=gaia_data[0]['pmRA'],
                    error=gaia_data[0]['e_pmRA'],
                    unit='mas',
                )

            #   DEC proper motion
            if (str(gaia_data[0]['pmDE']) != '--' and
                str(gaia_data[0]['e_pmDE']) != '--'):
                sobj.parameter_set.create(
                    data_source=dsgaia,
                    name='pmdec',
                    component=0,
                    value=gaia_data[0]['pmDE'],
                    error=gaia_data[0]['e_pmDE'],
                    unit='mas',
                )
    else:
        if (star['parallax'] != None or
            star['pmra_x'] != None or
            star['pmdec_x'] != None):

            try:
                dsgaia = DataSource.objects.get(
                    name__exact='Gaia DR2',
                    project=project,
                )
            except DataSource.DoesNotExist:
                dsgaia = DataSource.objects.create(
                    name='Gaia DR2',
                    note='2nd Gaia data release',
                    reference='https://doi.org/10.1051/0004-6361/201833051',
                    project=project,
                )

            #   Set parallax
            if star['parallax'] != None:
                sobj.parameter_set.create(
                    data_source=dsgaia,
                    name='parallax',
                    component=0,
                    value=star['parallax'],
                    error=star['parallax_error'],
                    unit='',
                )

            #   RA proper motion
            if star['pmra_x'] != None:
                sobj.parameter_set.create(
                    data_source=dsgaia,
                    name='pmra',
                    component=0,
                    value=star['pmra_x'],
                    error=star['pmra_error'],
                    unit='mas',
                )

            #   DEC proper motion
            if star['pmdec_x'] != None:
                sobj.parameter_set.create(
                    data_source=dsgaia,
                    name='pmdec',
                    component=0,
                    value=star['pmdec_x'],
                    error=star['pmdec_error'],
                    unit='mas',
                )

    sobj.save()

    return True, "New system ({}) created".format(star["main_id"])
