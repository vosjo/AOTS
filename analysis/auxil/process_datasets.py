from django.db.models import F, ExpressionWrapper, FloatField
import random
from analysis.models import DataSource, DataSet, Method, DerivedParameter
from stars.models import Star
from . import read_datasets


def create_parameters(analmethod, data):
    """
    Adds all parameters from the analfile
    """
    parameters = read_datasets.get_parameters(data)
    for name, value in parameters.items():
        if name == 't0':
            # exception for t0 as this 0 ending might cause problems
            name = 't00'

        component = 0
        if name[-1] in ['0', '1', '2']:
            component = int(name[-1])
            name = name[:-1]

        analmethod.parameter_set.create(name=name, component=component, value=value[0],
                                        error_u=value[1], error_l=value[2],
                                        unit=value[3], star=analmethod.star)

    return len(parameters.keys())


def create_derived_parameters(analmethod):
    """
    Adds the parameters that can be automatically derived for this method
    """

    try:
        ds = DataSource.objects.get(name__exact='AVG')
    except DataSource.DoesNotExist:
        ds = DataSource.objects.create(name='AVG')

    params = analmethod.method.derived_parameters
    if params.strip() == '': return 0

    params = params.split(',')
    for p in params:
        p = p.strip()
        if '_' in p:
            pname = p.split('_')[-2]
            pcomp = int(p.split('_')[-1])
        elif p[-1] in ['0', '1', '2']:
            pname = p[:-1]
            pcomp = int(p[-1])
        else:
            pname = p
            pcomp = 0

        p = DerivedParameter.objects.create(star=analmethod.star, name=pname,
                                            component=pcomp, average=True,
                                            data_source=ds)
        print(p)

    return len(params)


def sort_modified_created(model):
    try:
        return model.history.latest().history_date
    except AttributeError:
        return datetime.fromisoformat("19700101")


def process_analysis_file(file_id):
    #   analfile == dataset
    analfile = DataSet.objects.get(pk=file_id)

    try:
        data = analfile.get_data()
    except Exception as e:
        return False, 'Not added, file has wrong format / file is unreadable'

    # read the basic data
    try:
        systemname, ra, dec, name, note, reference, atype = read_datasets.get_basic_info(data)
    except Exception as e:
        print(e)
        return False, 'Not added, basic info unreadable'

    #   Filter Method for project and slug
    d_method = Method.objects.filter(slug__exact=atype)
    d_method = d_method.filter(project__exact=analfile.project)

    #   If there is an existing method, pick the first
    message = ''
    if d_method:
        analfile.method = d_method[0]
    else:
        #   Random number function for color
        r = lambda: random.randint(0,255)

        #   Create a new method
        method = Method(
            name = name,
            project=analfile.project,
            slug = atype,
            color=f'#{r():02x}{r():02x}{r():02x}',
            )
        method.save()
        analfile.method = method
        message += f"Created new Method {method},"

    analfile.name = name
    analfile.note = note
    analfile.reference = reference

    analfile.save()

    # -- try to find corresponding star
    if ra != 0.0 and dec != 0.0:
        star = Star.objects.filter(ra__range=(ra - 0.01, ra + 0.01),
                                   dec__range=(dec - 0.01, dec + 0.01),
                                   project__exact=analfile.project.pk)
    else:
        star = Star.objects.filter(
            name__iexact=systemname,
            project__exact=analfile.project.pk,
            )
        if not star:
            #   There is no way to add this star, cause no coordinates are
            #   known.
            return False, "Not added, no system information present"

    message += "Validated the analysis file"
    if star:
        #   There is an existing star, pick the closest star
        star = star.annotate(
            distance = ExpressionWrapper(
                ((F('ra') - ra) ** 2 + (F('dec') - dec) ** 2) ** (1. / 2.),
                output_field=FloatField()
                )
            ).order_by('distance')[0]
        star.dataset_set.add(analfile)
        message += f", added to existing System {star} "
        message += f"(_r = {star.distance})"
    else:
        #   Need to create a new star
        star = Star(
            name=systemname,
            project=analfile.project,
            ra=ra,
            dec=dec,
            classification='',
            )
        star.save()
        star.dataset_set.add(analfile)
        message += ", created new System {}".format(star)

    # -- Add parameters
    try:
        npars = create_parameters(analfile, data)
        if npars == 0:
            analfile.valid = False
            analfile.save()
            message += ", (No parameters included, default to invalid dataset)"
        else:
            message += ", ({} parameters)".format(npars)
    except Exception as e:
        raise e
        return False, 'Not added, error reading parameters'

    ##-- add derived parameters
    # npars = create_derived_parameters(analfile)
    # if npars > 0: message += ", ({} derived parameters)".format(npars)

    # -- Check if star already has this type of dataset, if so, replace
    #   only do so at the end so only valid datasets can replace an old one.
    similar = sorted(DataSet.objects.filter(
        method__exact=analfile.method,
        star__exact=star,
        project__exact=analfile.project.pk,
        ), key=sort_modified_created, reverse=True)

    if len(similar) > 1:
        #   Update old dataset entry
        similar[0].name = analfile.name
        similar[0].note = analfile.note
        similar[0].reference = analfile.reference
        similar[0].method = analfile.method
        similar[0].datafile = analfile.datafile
        similar[0].valid = analfile.valid
        similar[0].history.latest().history_user.username = analfile.history.earliest().history_user.username
        similar[0].save()

        #   Remove new dataset since it is not needed
        analfile.delete()

        message += ", replaced older analysis method"

    return True, message
