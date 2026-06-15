from analysis.models.default_values import PARAMETER_DECIMALS, STELLAR_PARAMETERS, SYSTEM
from analysis.models.parameters import Parameter


def get_system_parameters(analysis):
    parameters = Parameter.objects.filter(analysis=analysis, component__exact=SYSTEM)
    pars = []
    for p in parameters.order_by('name'):
        prec = PARAMETER_DECIMALS.get(p.name, 3)
        pars.append(
            (p.name, p.unit, "{: > 6.{prec}f} &pm; {: > 6.{prec}f}".format(p.rvalue(), p.rerror(), prec=prec))
        )
    return pars


def get_component_parameters(analysis):
    parameters = set(
        Parameter.objects.filter(
            analysis=analysis,
            component__in=STELLAR_PARAMETERS,
        ).values_list('name', flat=True)
    )
    pars = []
    for pname in parameters:
        qset = Parameter.objects.filter(analysis=analysis, name__exact=pname)

        line = [pname, qset[0].unit]
        for comp in STELLAR_PARAMETERS:
            p = qset.filter(component__exact=comp)

            if p:
                prec = PARAMETER_DECIMALS.get(p[0].name, 3)
                line.append(
                    "{: > 5.{prec}f} &pm; {: > 5.{prec}f}".format(p[0].rvalue(), p[0].rerror(), prec=prec)
                )
            else:
                line.append(r" / ")

        pars.append(tuple(line))
    return pars
