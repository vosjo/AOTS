from analysis.categories import category_derived_parameters, parse_derived_parameter_specs
from analysis.models import DerivedParameter
from analysis.services.parameter_sources import get_or_create_avg_source
from . import read_analyses


def create_parameters(analmethod, data):
    """Adds all parameters from the analfile."""
    parameters = read_analyses.get_parameters(data)
    for name, value in parameters.items():
        if name == 't0':
            name = 't00'

        component = 0
        if name[-1] in ['0', '1', '2']:
            component = int(name[-1])
            name = name[:-1]

        analmethod.parameter_set.create(
            name=name,
            component=component,
            value=value[0],
            error_u=value[1],
            error_l=value[2],
            unit=value[3],
            star=analmethod.star,
            analysis=analmethod,
        )

    return len(parameters.keys())


def create_derived_parameters(analmethod):
    """Adds category-configured derived parameters for the analysis star."""
    from analysis.categories import category_derived_parameters

    ds = get_or_create_avg_source(analmethod.project)

    params = category_derived_parameters(analmethod.category)
    if params.strip() == '':
        return 0

    created = 0
    for pname, pcomp in parse_derived_parameter_specs(params):
        if DerivedParameter.objects.filter(
            star=analmethod.star,
            name=pname,
            component=pcomp,
            average=True,
        ).exists():
            continue

        DerivedParameter.objects.create(
            star=analmethod.star,
            name=pname,
            component=pcomp,
            average=True,
            parameter_source=ds,
        )
        created += 1

    return created


def process_analysis_file(file_id):
    from analysis.services.analysis_ingestion import ingest_analysis_file
    result = ingest_analysis_file(file_id)
    return result.success, result.message
