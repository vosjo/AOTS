import numpy as np
from astropy.coordinates.angles import Angle
from astropy.io import fits
from scipy import stats

from analysis.auxil.apiprocessing import find_or_create_star
from analysis.models.SEDs import SED
from analysis.models.rvcurves import RVcurve
from stars.models import Star


# from .models import DataSet


def create_parameters(analmethod, parameters):
    """
    Adds all parameters from the analfile
    """
    for key, value in parameters.items():
        name = key
        value, error, unit = float(value[0]), float(value[1]), str(value[2])
        analmethod.parameter_set.create(name=name, value=value, error=error, unit=unit,
                                        star=analmethod.star)


# def process_analysis_file(file_id):
#     analfile = DataSet.objects.get(pk=file_id)
#
#     data = analfile.get_data()
#
#     # -- check if name or coordinates are present
#     if not 'ra' in data or not 'dec' in data:
#         analfile.delete()
#         return False, "Could not add file as System info was not present"
#
#     # -- type to read some basic info
#     if 'type' in data:
#         analfile.analysis_type = data['type']
#
#     if 'note' in data:
#         analfile.note = data['note']
#
#     if 'name' in data:
#         analfile.name = data['name']
#
#     analfile.save()
#
#     message = "Validated the analysis file"
#
#     # -- match to an existing star, or create a new one
#     if type(data['ra']) == str:
#         ra = Angle(data['ra'], unit='hour').degree
#         dec = Angle(data['dec'], unit='degree').degree
#     else:
#         ra, dec = data['ra'], data['dec']
#
#     star = Star.objects.filter(ra__range=(ra - 0.01, ra + 0.01)) \
#         .filter(dec__range=(dec - 0.01, dec + 0.01))
#
#     if len(star) > 0:
#         # there is an existing star
#         star = star[0]
#         star.dataset_set.add(analfile)
#         message += ", added to existing System {}".format(star)
#     else:
#         # Need to create a new star
#         star = Star(name=data['name'], ra=ra, dec=dec, classification='')
#         star.save()
#         star.dataset_set.add(analfile)
#         message += ", created new System {}".format(star)
#
#     # -- add parameters
#     create_parameters(analfile, data['PARAMETERS'])
#     message += ", added {} parameters".format(len(data['PARAMETERS'].keys()))
#
#     return True, message


def calculate_logp(vrad, vrad_err):
    """
    :param vrad: Radial Velocity array
    :param vrad_err: Array of corresponding Errors
    :return: logp value
    """
    ndata = len(vrad)
    if ndata < 2:
        return np.nan
    nfit = 1

    vrad_wmean = np.sum(vrad / vrad_err) / np.sum(1 / vrad_err)

    chi = (vrad - vrad_wmean) / vrad_err

    chisq = chi ** 2
    chisq_sum = np.sum(chisq)

    dof = ndata - nfit

    pval = stats.chi2.sf(chisq_sum, dof)
    logp = np.log10(pval)

    if pval == 0:
        return -500
    if np.isnan(logp):
        return 0

    return logp


def get_key_or_blank(dictionary, key):
    try:
        return dictionary[key]
    except KeyError:
        return 0


def process_rvcurvefiles(files, project, handle_double=None):
    returned_messages = []
    n_exceptions = 0
    for f in files:
        test = fits.open(f)
        metadata = dict(test[0].header)
        datapoints = np.array(list(test[1].data))
        datainfo = dict(test[1].header)
        column_names = []
        n = 1
        while True:
            if "TTYPE" + str(n) in datainfo:
                column_names.append(datainfo["TTYPE" + str(n)])
                n += 1
            else:
                break

        rvs = datapoints[:, column_names.index("RV")]
        rvs_err = datapoints[:, column_names.index("RVERR")]
        times = datapoints[:, column_names.index("MJD")]

        try:
            curveexists = RVcurve.objects.get(average_rv__exact=np.mean(rvs),
                                              time_spanned__exact=np.ptp(times),
                                              delta_rv=np.ptp(rvs))
            if handle_double == "overwrite":
                curveexists.delete()
            if handle_double == "append":
                # TODO: add append action
                pass
        except:
            n_exceptions += 1
            returned_messages.append(f"RV Curve with average RV {np.mean(rvs)} already exists, please specify if you want to append or overwrite!")

        if "LOGP" not in metadata or np.isnan(metadata["LOGP"]):
            metadata["LOGP"] = calculate_logp(rvs, rvs_err)

        if "RVAVG" not in metadata or np.isnan(metadata["RVAVG"]):
            metadata["RVAVG"] = np.mean(rvs)

        if "U_RVAVG" not in metadata or np.isnan(metadata["U_RVAVG"]):
            metadata["U_RVAVG"] = np.sqrt(np.sum(np.square(rvs_err)))

        if "DRV" not in metadata or np.isnan(metadata["DRV"]):
            metadata["DRV"] = np.ptp(rvs)

        if "U_DRV" not in metadata or np.isnan(metadata["U_DRV"]):
            metadata["U_DRV"] = np.sqrt(rvs[np.argmax(rvs)] ** 2 + rvs[np.argmin(rvs)] ** 2) / 2

        if "NSPEC" not in metadata or np.isnan(metadata["NSPEC"]):
            metadata["NSPEC"] = len(rvs)

        if "TSPAN" not in metadata or np.isnan(metadata["TSPAN"]):
            metadata["TSPAN"] = np.ptp(times)

        newrvcurve = RVcurve(
            sourcefile=f,
            average_rv=get_key_or_blank(metadata, "RVAVG"),
            average_rv_err=get_key_or_blank(metadata, "U_RVAVG"),
            delta_rv=get_key_or_blank(metadata, "DRV"),
            delta_rv_err=get_key_or_blank(metadata, "U_DRV"),
            logp=get_key_or_blank(metadata, "LOGP"),
            N_samples=get_key_or_blank(metadata, "NSPEC"),
            time_spanned=get_key_or_blank(metadata, "TSPAN"),
            project=project,
        )
        newrvcurve.save()

        success, msg, star = find_or_create_star(metadata, project, newrvcurve, modeltype="RV")

        if success:
            returned_messages.append(f"Successfully added RV curve to star {star.name}")
        else:
            n_exceptions += 1
            returned_messages.append(f"Something went wrong for file {f}")
    return returned_messages, n_exceptions


def process_SEDfiles(files, project, handle_double=None, update_star=False):
    returned_messages = []
    n_exceptions = 0
    for f in files:
        test = fits.open(f)
        metadata = dict(test[0].header)

        # try:
        curveexists = SED.objects.get(teff__exact=metadata["TEFF"],
                                      logg__exact=metadata["LOGG"],
                                      metallicity__exact=metadata['METAL'])
        if handle_double == "overwrite":
            curveexists.delete()
        # except:
        #     n_exceptions += 1
        #     returned_messages.append(f"SED with effective Temperature {metadata['TEFF']}, logg {metadata['LOGG']} and "
        #                              f"metallicity {metadata['METAL']} already exists, please specify if you want to "
        #                              f"append or overwrite!")

        newSED = SED(
            sourcefile=f,
            teff=get_key_or_blank(metadata, "TEFF"),
            teff_lerr=get_key_or_blank(metadata, "TEFF_LE"),
            teff_uerr=get_key_or_blank(metadata, "TEFF_UE"),
            logg=get_key_or_blank(metadata, "LOGG"),
            logg_lerr=get_key_or_blank(metadata, "LOGG_LE"),
            logg_uerr=get_key_or_blank(metadata, "LOGG_UE"),
            metallicity=get_key_or_blank(metadata, "METAL"),
            metallicity_lerr=get_key_or_blank(metadata, "METAL_LE"),
            metallicity_uerr=get_key_or_blank(metadata, "METAL_UE"),
            color_excess=get_key_or_blank(metadata, "CEX"),
            color_excess_lerr=get_key_or_blank(metadata, "CEX_LE"),
            color_excess_uerr=get_key_or_blank(metadata, "CEX_UE"),
            logtheta=get_key_or_blank(metadata, "LOGT"),
            logtheta_lerr=get_key_or_blank(metadata, "LOGT_LE"),
            logtheta_uerr=get_key_or_blank(metadata, "LOGT_UE"),
            project=project,
        )
        newSED.save()

        if update_star:
            success, msg, star = find_or_create_star(metadata, project, newSED, "SED", True)
        else:
            success, msg, star = find_or_create_star(metadata, project, newSED, "SED")

        if success:
            returned_messages.append(f"Successfully added SED to star {star.name}")
        else:
            n_exceptions += 1
            returned_messages.append(f"Something went wrong for file {f}")
    return returned_messages, n_exceptions