from analysis.categories import CategorySource, resolve_category
from analysis.models import DataSource, DataSet, DerivedParameter
from stars.models import Star
from django.db.models import F, ExpressionWrapper, FloatField
from . import read_datasets


def create_parameters(analmethod, data):
    """
    Adds all parameters from the analfile
    """
    parameters = read_datasets.get_parameters(data)
    for name, value in parameters.items():
        if name == 't0':
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
    Adds the parameters that can be automatically derived for this dataset category.
    """
    from analysis.categories import category_derived_parameters

    try:
        ds = DataSource.objects.get(name__exact='AVG')
    except DataSource.DoesNotExist:
        ds = DataSource.objects.create(name='AVG')

    params = category_derived_parameters(analmethod.category)
    if params.strip() == '':
        return 0

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

        DerivedParameter.objects.create(star=analmethod.star, name=pname,
                                      component=pcomp, average=True,
                                      data_source=ds)

    return len(params)


def process_analysis_file(file_id):
    analfile = DataSet.objects.get(pk=file_id)

    try:
        data = analfile.get_data()
    except Exception:
        return False, 'Not added, file has wrong format / file is unreadable'

    try:
        systemname, ra, dec, name, note, reference, atype = read_datasets.get_basic_info(data)
    except Exception as e:
        print(e)
        return False, 'Not added, basic info unreadable'

    category, category_source = resolve_category(atype)
    analfile.category = category
    analfile.category_source = category_source
    analfile.file_type = atype or ''
    analfile.name = name
    analfile.note = note
    analfile.reference = reference
    analfile.save()

    message = 'Validated the analysis file'

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
            return False, "Not added, no system information present"

    if star:
        star = star.annotate(
            distance=ExpressionWrapper(
                ((F('ra') - ra) ** 2 + (F('dec') - dec) ** 2) ** (1. / 2.),
                output_field=FloatField()
            )
        ).order_by('distance')[0]
        analfile.star = star
        analfile.save()
        message += f", added to existing System {star} (_r = {star.distance})"
    else:
        star = Star(
            name=systemname,
            project=analfile.project,
            ra=ra,
            dec=dec,
            classification='',
        )
        star.save()
        analfile.star = star
        analfile.save()
        message += ", created new System {}".format(star)

    try:
        npars = create_parameters(analfile, data)
        if npars == 0:
            analfile.fit = False
            analfile.save()
            message += ", (No parameters included, no fit)"
        else:
            message += ", ({} parameters)".format(npars)
    except Exception as e:
        raise e

    return True, message
