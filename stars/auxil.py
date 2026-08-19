import astropy.units as u
import numpy as np
from astropy.coordinates import SkyCoord
from astropy.coordinates.angles import Angle
from astroquery.simbad import Simbad
from astroquery.vizier import Vizier
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, reverse

from analysis import models as analModels
from analysis.models import ParameterSource
from analysis.services import parameter_io
from stars.photometry_bands import (
    CSV_ERR_BY_BAND,
    CSV_MAG_BY_BAND,
    CSV_MAG_TO_BAND,
    build_vizier_catalogs,
    csv_import_bands,
    errs,
    photnames,
)
from stars.photometry_bands import (
    PASSBANDS as passbands,
)
from stars.services import star_io

from .models import Star

catalogs = build_vizier_catalogs()


def invalid_form(request, redirect, project_slug, star_id=None):
    """
        Handle invalid forms
    """
    #   Add message
    messages.add_message(
        request,
        messages.ERROR,
        "Invalid form. Please try again.",
    )
    print("Invalid form...")
    #   Return and redirect
    if star_id:
        return HttpResponseRedirect(
            reverse(redirect, kwargs={'project': project_slug,
                                      "star_id": star_id})
        )
    else:
        return HttpResponseRedirect(
            reverse(redirect, kwargs={'project': project_slug})
        )


def _simbad_colnames(row):
    return list(row.colnames) if hasattr(row, 'colnames') else list(row.keys())


def _simbad_field(row, *names):
    colnames = _simbad_colnames(row)
    lower_map = {col.lower(): col for col in colnames}
    for name in names:
        key = lower_map.get(name.lower())
        if key is None:
            continue
        val = row[key]
        if val is None or (isinstance(val, (float, np.floating)) and np.isnan(val)):
            return ''
        if isinstance(val, str):
            return val.strip()
        return val
    return ''


def _simbad_coords_deg(row):
    ra_val = _simbad_field(row, 'ra', 'RA')
    dec_val = _simbad_field(row, 'dec', 'DEC')
    if isinstance(ra_val, (float, int, np.floating, np.integer)):
        return float(ra_val), float(dec_val)
    ra = Angle(str(ra_val).strip(), unit='hour').degree
    dec = Angle(str(dec_val).strip(), unit='degree').degree
    return ra, dec


def format_ra_hms(ra_deg):
    return Angle(ra_deg, unit='deg').to_string(
        unit='hourangle', sep=':', precision=1, pad=True,
    )


def format_dec_dms(dec_deg):
    return Angle(dec_deg, unit='deg').to_string(
        unit='deg', sep=':', alwayssign=True, precision=1, pad=True,
    )


def _simbad_match_payload(row):
    ra_deg, dec_deg = _simbad_coords_deg(row)
    sp_type = str(_simbad_field(row, 'sp_type', 'SP_TYPE', 'sptype') or '').strip()
    return {
        'main_id': str(_simbad_field(row, 'main_id', 'MAIN_ID') or '').strip(),
        'ra': str(format_ra_hms(ra_deg)),
        'dec': str(format_dec_dms(dec_deg)),
        'classification': sp_type,
        'classification_type': Star.SPECTROSCOPIC if sp_type else Star.PHOTOMETRIC,
    }


def query_simbad_object(name):
    custom = Simbad()
    custom.add_votable_fields('sp_type')
    try:
        tbl = custom.query_object(name)
    except Exception:
        return None
    if tbl is None or len(tbl) == 0:
        return None
    return tbl[0]


def resolve_simbad_name(name):
    name = (name or '').strip()
    if not name:
        return {'status': 'empty'}

    esc = name.replace("'", "''")
    tap_query = (
        "SELECT DISTINCT TOP 25 b.oid, b.main_id, b.ra, b.dec, b.sp_type "
        "FROM ident AS i JOIN basic AS b ON b.oid = i.oidref "
        f"WHERE i.id = '{esc}'"
    )
    try:
        tap = Simbad.query_tap(tap_query)
    except Exception:
        tap = None

    if tap is not None and len(tap) == 1:
        return {'status': 'unique', **_simbad_match_payload(tap[0])}

    if tap is not None and len(tap) > 1:
        return {
            'status': 'ambiguous',
            'matches': [_simbad_match_payload(row) for row in tap],
        }

    row = query_simbad_object(name)
    if row is None:
        return {'status': 'not_found'}

    return {'status': 'unique', 'best_match': True, **_simbad_match_payload(row)}


def populate_system(star, star_pk):
    """
        Analyse provided 'star' dictionary and create a Star object
    """
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

    simbad_main_id = ''
    #   Coordinates
    if check_vizier:
        row = query_simbad_object(star["main_id"])
        if row is None:
            return False, "System ({}) not known by Simbad".format(
                star["main_id"]
            )
        ra, dec = _simbad_coords_deg(row)
        simbad_main_id = str(_simbad_field(row, 'main_id', 'MAIN_ID') or '').strip()
        sp_type = str(_simbad_field(row, 'sp_type', 'SP_TYPE', 'sptype') or '').strip()
    else:
        ra = float(star['ra'])
        dec = float(star['dec'])
        sp_type = star.get('sp_type', '')

    #   Set RA & DEC
    sobj.ra = ra
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
        sobj.classification = sp_type
        if sp_type:
            sobj.classification_type = 'SP'
    else:
        sobj.classification = star['sp_type']
        if 'classification_type' in star:
            sobj.classification_type = star['classification_type']

    #   Set identifier
    ident = sobj.identifier_set.all()[0]
    ident.href = "https://simbad.u-strasbg.fr/simbad/" \
                 + "sim-id?Ident=" + star['main_id'] \
                     .replace(" ", "").replace('+', "%2B")
    ident.save()

    #   Add JNAME as identifier if provided
    if 'JNAME' in star:
        sobj.identifier_set.create(name=star['JNAME'])

    #   Add default Simbad name if query occurred
    #   and if it is different compared to the provided name
    if check_vizier:
        if simbad_main_id and star["main_id"].strip() != simbad_main_id:
            sobj.identifier_set.create(
                name=simbad_main_id,
                href="https://simbad.u-strasbg.fr/simbad/"
                     + "sim-id?Ident=" + simbad_main_id
                     .replace(" ", "").replace('+', "%2B"),
            )

    # -- Add Tags
    if 'tags' in star:
        for tag in star["tags"]:
            sobj.tags.add(tag)

    if check_vizier:
        _store_vizier_photometry(sobj, ra, dec)
    else:
        _store_csv_photometry(sobj, star)

    if check_vizier:
        #   Download GAIA DR3 data
        gaia_data = Vizier(
            catalog='I/355/gaiadr3',
            columns=['Plx', 'e_Plx', 'pmRA', 'e_pmRA', 'pmDE', 'e_pmDE'],
        ).query_region(star["main_id"], radius=1 * u.arcsec)

        #   Check if GAIA data is available for the source
        if len(gaia_data) != 0:
            #   Set data source
            try:
                dsgaia = ParameterSource.objects.get(
                    name__exact='Gaia DR3',
                    project=project,
                )
            except ParameterSource.DoesNotExist:
                dsgaia = ParameterSource.objects.create(
                    name='Gaia DR3',
                    note='3nd Gaia data release',
                    reference='https://doi.org/10.1051/0004-6361/202243940',
                    project=project,
                )

            #   Set parallax
            if (str(gaia_data[0]['Plx']) != '--' and
                    str(gaia_data[0]['e_Plx']) != '--'):
                parameter_io.create_measurement(
                    star=sobj,
                    parameter_source=dsgaia,
                    name='parallax',
                    component=0,
                    value=gaia_data[0]['Plx'],
                    error_l=gaia_data[0]['e_Plx'],
                    error_u=gaia_data[0]['e_Plx'],
                    unit='',
                    run_after=False,
                )

            #   RA proper motion
            if (str(gaia_data[0]['pmRA']) != '--' and
                    str(gaia_data[0]['e_pmRA']) != '--'):
                parameter_io.create_measurement(
                    star=sobj,
                    parameter_source=dsgaia,
                    name='pmra',
                    component=0,
                    value=gaia_data[0]['pmRA'],
                    error_l=gaia_data[0]['e_pmRA'],
                    error_u=gaia_data[0]['e_pmRA'],
                    unit='mas',
                    run_after=False,
                )

            #   DEC proper motion
            if (str(gaia_data[0]['pmDE']) != '--' and
                    str(gaia_data[0]['e_pmDE']) != '--'):
                parameter_io.create_measurement(
                    star=sobj,
                    parameter_source=dsgaia,
                    name='pmdec',
                    component=0,
                    value=gaia_data[0]['pmDE'],
                    error_l=gaia_data[0]['e_pmDE'],
                    error_u=gaia_data[0]['e_pmDE'],
                    unit='mas',
                    run_after=False,
                )
    else:
        if (star['parallax'] is not None or
                star['pmra_x'] is not None or
                star['pmdec_x'] is not None):

            try:
                dsgaia = ParameterSource.objects.get(
                    name__exact='Gaia DR3',
                    project=project,
                )
            except ParameterSource.DoesNotExist:
                dsgaia = ParameterSource.objects.create(
                    name='Gaia DR3',
                    note='3nd Gaia data release',
                    reference='https://doi.org/10.1051/0004-6361/202243940',
                    project=project,
                )

            #   Set parallax
            if star['parallax'] is not None:
                parameter_io.create_measurement(
                    star=sobj,
                    parameter_source=dsgaia,
                    name='parallax',
                    component=0,
                    value=star['parallax'],
                    error_l=star['parallax_error'],
                    error_u=star['parallax_error'],
                    unit='',
                    run_after=False,
                )

            #   RA proper motion
            if star['pmra_x'] is not None:
                parameter_io.create_measurement(
                    star=sobj,
                    parameter_source=dsgaia,
                    name='pmra',
                    component=0,
                    value=star['pmra_x'],
                    error_l=star['pmra_error'],
                    error_u=star['pmra_error'],
                    unit='mas',
                    run_after=False,
                )

            #   DEC proper motion
            if star['pmdec_x'] is not None:
                parameter_io.create_measurement(
                    star=sobj,
                    parameter_source=dsgaia,
                    name='pmdec',
                    component=0,
                    value=star['pmdec_x'],
                    error_l=star['pmdec_error'],
                    error_u=star['pmdec_error'],
                    unit='mas',
                    run_after=False,
                )

    parameter_io.after_star_parameters_batch(sobj)
    star_io.save_star(sobj)

    return True, "New system ({}) created".format(star["main_id"])


def _resolve_vizier_column(photo_row, column):
    """Map registry column name to actual VizieR table column (handles g'mag vs g_mag)."""
    colnames = list(photo_row.colnames)
    candidates = (column, column.replace("'", '_'), column.replace("'", ''))
    for cand in candidates:
        if cand in colnames:
            return cand
    lower_map = {name.lower(): name for name in colnames}
    for cand in candidates:
        match = lower_map.get(cand.lower())
        if match:
            return match
    raise KeyError(column.replace("'", '_'))


def _vizier_mag_err(photo_row, column, err_column):
    try:
        band_col = _resolve_vizier_column(photo_row, column)
        err_col = _resolve_vizier_column(photo_row, err_column)
    except KeyError:
        return None
    mag = photo_row[band_col][0]
    err = photo_row[err_col][0]
    if str(err) == '--' or np.isnan(err):
        err = 0.
    if mag != '--' and not np.isnan(mag):
        return float(mag), float(err)
    return None


def _store_vizier_photometry(star_obj, ra, dec, *, replace_existing=False):
    for content in catalogs.values():
        try:
            v = Vizier(
                catalog=content['simbad_id'],
                columns=content['columns'] + content['err_columns'],
            )
            photo = v.query_region(
                SkyCoord(ra=ra, dec=dec, unit=(u.deg, u.deg), frame='icrs'),
                radius=1 * u.arcsec,
            )
        except Exception:
            continue
        if len(photo) == 0:
            continue
        for i, column in enumerate(content['columns']):
            values = _vizier_mag_err(photo[0], column, content['err_columns'][i])
            if values is None:
                continue
            mag, err = values
            band_id = content['passbands'][i]
            if replace_existing:
                star_obj.photometry_set.filter(band=band_id).delete()
            star_obj.photometry_set.create(
                band=band_id,
                measurement=mag,
                error=err,
                unit='mag',
            )


def _csv_photometry_value(row, csv_mag, csv_err):
    if csv_mag not in row:
        return None
    value = row[csv_mag]
    if value is None or value == '':
        return None
    if csv_err in row and row[csv_err] not in (None, ''):
        return float(value), float(row[csv_err])
    return float(value), 0.0


def _store_csv_photometry(star_obj, row):
    for band in csv_import_bands():
        values = _csv_photometry_value(row, band.csv_mag, band.csv_err)
        if values is None:
            continue
        mag, err = values
        star_obj.photometry_set.create(
            band=band.id,
            measurement=mag,
            error=err,
            unit='mag',
        )


def update_photometry(cleaned_data, project, star_id, from_vizier):
    star = get_object_or_404(Star, pk=star_id)
    if not from_vizier:
        for csv_mag, band_id in CSV_MAG_TO_BAND.items():
            if csv_mag not in cleaned_data:
                continue
            pval = cleaned_data[csv_mag]
            phset = star.photometry_set.filter(band=band_id)
            if pval is None:
                if phset.exists():
                    phset.first().delete()
            else:
                err_key = CSV_ERR_BY_BAND[band_id]
                err_val = cleaned_data.get(err_key, 0)
                phset.delete()
                star.photometry_set.create(
                    band=band_id,
                    measurement=pval,
                    error=err_val,
                    unit='mag',
                )
        return True, ''
    else:
        from stars.services.vizier_photometry import import_photometry_from_vizier_for_star

        result = import_photometry_from_vizier_for_star(star)
        if result.status == 'error':
            return False, result.message
        return True, result.message


def _parameter_display_value(param) -> str:
    return rf"{param.rvalue()} &pm; {param.rerror()}"


def _consensus_result_display(name: str, result) -> str:
    from analysis.models.default_values import round_value

    error = result.error_l if result.error_l == result.error_u else result.error_l
    return rf"{round_value(result.value, name, result.error_l)} &pm; {round_value(error, name, result.error_l)}"


def _parameter_provenance_label(param) -> str:
    if param.analysis_id:
        return param.analysis.name
    if param.parameter_source_id:
        return param.parameter_source.name
    return ''


#   Get all parameters for the parameter overview
def get_params(star_id, *, catalog_only=False):
    from django.db.models import Q

    from analysis.models.parameter_source import ParameterSourceKind
    from analysis.services.parameter_consensus import (
        consensus_provenance_display,
        get_consensus_parameter,
        list_other_measurements,
        provenance_label_for_parameter,
        resolve_catalog_consensus,
        resolve_consensus,
    )

    star = get_object_or_404(Star, pk=star_id)
    parameters = []
    component_names = {0: 'System', 1: 'Primary', 2: 'Secondary'}
    resolve = resolve_catalog_consensus if catalog_only else resolve_consensus

    for comp in [analModels.SYSTEM, analModels.PRIMARY, analModels.SECONDARY]:
        base_qs = star.parameter_set.filter(
            component__exact=comp,
            valid__exact=True,
            average=False,
        )
        if catalog_only:
            name_qs = base_qs.filter(parameter_source__kind=ParameterSourceKind.CATALOG)
        else:
            name_qs = base_qs.filter(
                Q(analysis__isnull=False)
                | Q(parameter_source__kind=ParameterSourceKind.CATALOG),
            )
        pNames = sorted(
            name_qs.values_list('name', flat=True).distinct(),
            key=analModels.parameter_order,
        )

        params = []
        for name in pNames:
            consensus = get_consensus_parameter(star, name, comp)
            result = resolve(star, name, comp)
            pinfo = name_qs.filter(name__exact=name).first()

            if consensus:
                display_value = _parameter_display_value(consensus)
                provenance = consensus_provenance_display(star, consensus, name, comp)
            elif result:
                display_value = _consensus_result_display(name, result)
                provenance = result.provenance_label
            elif pinfo:
                display_value = _parameter_display_value(pinfo)
                provenance = provenance_label_for_parameter(pinfo)
            else:
                continue

            row_pinfo = pinfo or consensus
            others = [
                {
                    'parameter_id': param.pk,
                    'value': _parameter_display_value(param),
                    'provenance': provenance_label_for_parameter(param),
                }
                for param in list_other_measurements(
                    star, name, comp, catalog_only=catalog_only,
                )
            ]

            params.append({
                'value': display_value,
                'pinfo': row_pinfo,
                'provenance': provenance,
                'other_measurements': others,
            })

        parameters.append({'params': params, 'component': component_names[comp]})
    return parameters


def pk_from_source_name(sname, star):
    pSource_pks = star.parameter_set.values_list('parameter_source').distinct()
    for i in pSource_pks:
        pSource = ParameterSource.objects.filter(id__in=i)
        if pSource[0].name == sname:
            return i, pSource[0]


def update_parameters(cleaned_data, project, star_id):
    star = get_object_or_404(Star, pk=star_id)
    for key, val in cleaned_data.items():
        if "err" not in key:
            name, comp, source = key.split("_")
            errname = key.split("_")
            errname[0] += "-err"
            errname = "_".join(errname)
            errval = cleaned_data[errname]
            spk, dSource = pk_from_source_name(source, star)
            paramset = star.parameter_set.filter(name__exact=name, parameter_source__exact=spk)
            if len(paramset) != 0:
                parameter_io.delete_measurement(paramset[0], run_after=False)
            parameter_io.create_measurement(
                star=star,
                name=name,
                parameter_source=dSource,
                value=val,
                error_l=errval,
                error_u=errval,
                run_after=False,
            )
    parameter_io.after_star_parameters_batch(star)
    return True, ""
