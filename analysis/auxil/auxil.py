from astropy.coordinates.angles import Angle

from stars.models import Star
from .models import DataSet


def create_parameters(analmethod, parameters):
    """
    Adds all parameters from the analfile
    """
    for key, value in parameters.items():
        name = key
        value, error, unit = float(value[0]), float(value[1]), str(value[2])
        analmethod.parameter_set.create(name=name, value=value, error=error, unit=unit,
                                        star=analmethod.star)


def process_analysis_file(file_id):
    analfile = DataSet.objects.get(pk=file_id)

    data = analfile.get_data()

    # -- check if name or coordinates are present
    if not 'ra' in data or not 'dec' in data:
        analfile.delete()
        return False, "Could not add file as System info was not present"

    # -- type to read some basic info
    if 'type' in data:
        analfile.analysis_type = data['type']

    if 'note' in data:
        analfile.note = data['note']

    if 'name' in data:
        analfile.name = data['name']

    analfile.save()

    message = "Validated the analysis file"

    # -- match to an existing star, or create a new one
    if type(data['ra']) == str:
        ra = Angle(data['ra'], unit='hour').degree
        dec = Angle(data['dec'], unit='degree').degree
    else:
        ra, dec = data['ra'], data['dec']

    star = Star.objects.filter(ra__range=(ra - 0.01, ra + 0.01)) \
        .filter(dec__range=(dec - 0.01, dec + 0.01))

    if len(star) > 0:
        # there is an existing star
        star = star[0]
        star.dataset_set.add(analfile)
        message += ", added to existing System {}".format(star)
    else:
        # Need to create a new star
        star = Star(name=data['name'], ra=ra, dec=dec, classification='')
        star.save()
        star.dataset_set.add(analfile)
        message += ", created new System {}".format(star)

    # -- add parameters
    create_parameters(analfile, data['PARAMETERS'])
    message += ", added {} parameters".format(len(data['PARAMETERS'].keys()))

    return True, message
