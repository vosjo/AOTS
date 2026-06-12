from analysis.models import AverageDataSource


def get_or_create_avg_source(project) -> AverageDataSource:
    obj, _ = AverageDataSource.objects.get_or_create(
        project=project,
        name='AVG',
        defaults={},
    )
    return obj
