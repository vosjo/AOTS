from analysis.models import AverageParameterSource


def get_or_create_avg_source(project) -> AverageParameterSource:
    obj, _ = AverageParameterSource.objects.get_or_create(
        project=project,
        name='AVG',
        defaults={},
    )
    return obj
