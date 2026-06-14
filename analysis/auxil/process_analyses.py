from analysis.categories import CategorySource, resolve_category
from analysis.models import Analysis, DerivedParameter
from analysis.services.parameter_sources import get_or_create_avg_source
from stars.models import Star
from django.db.models import F, ExpressionWrapper, FloatField
from . import read_analyses


def create_parameters(analmethod, data):
    """
    Adds all parameters from the analfile
    """
    parameters = read_analyses.get_parameters(data)
    for name, value in parameters.items():
        if name == 't0':
            name = 't00'

        component = 0
        if name[-1] in ['0', '1', '2']:
            component = int(name[-1])
            name = name[:-1]

        analmethod.parameter_set.create(name=name, component=component, value=value[0],
                                        error_u=value[1], error_l=value[2],
                                        unit=value[3], star=analmethod.star,
                                        analysis=analmethod)

    return len(parameters.keys())


def create_derived_parameters(analmethod):
    """
    Adds the parameters that can be automatically derived for this analysis category.
    """
    from analysis.categories import category_derived_parameters

    ds = get_or_create_avg_source(analmethod.project)

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
                                      parameter_source=ds)

    return len(params)


def process_analysis_file(file_id):
    analfile = Analysis.objects.get(pk=file_id)

    try:
        data = analfile.get_data()
    except Exception:
        return False, 'Not added, file has wrong format / file is unreadable'

    try:
        systemname, ra, dec, name, note, reference, atype = read_analyses.get_basic_info(data)
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
