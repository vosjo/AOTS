from analysis.models import ParameterSource, ParameterSourceKind


def get_or_create_avg_source(project) -> ParameterSource:
    obj, _ = ParameterSource.objects.get_or_create(
        project=project,
        name='AVG',
        kind=ParameterSourceKind.AVERAGE,
        defaults={},
    )
    return obj
