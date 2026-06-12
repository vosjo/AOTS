from django.db import migrations


def unify_avg_sources(apps, schema_editor):
    DataSource = apps.get_model('analysis', 'DataSource')
    AverageDataSource = apps.get_model('analysis', 'AverageDataSource')
    Parameter = apps.get_model('analysis', 'Parameter')
    Project = apps.get_model('stars', 'Project')

    avg_by_project = {}
    for project in Project.objects.all():
        avg_source, _ = AverageDataSource.objects.get_or_create(
            project=project,
            name='AVG',
            defaults={},
        )
        avg_by_project[project.pk] = avg_source

    plain_avg_ids = []
    for ds in DataSource.objects.filter(name='AVG'):
        if AverageDataSource.objects.filter(datasource_ptr_id=ds.pk).exists():
            continue
        plain_avg_ids.append(ds.pk)

    for plain_id in plain_avg_ids:
        plain = DataSource.objects.get(pk=plain_id)
        params = Parameter.objects.filter(data_source_id=plain_id)
        if not params.exists():
            plain.delete()
            continue
        project_ids = params.values_list('star__project_id', flat=True).distinct()
        for project_id in project_ids:
            if project_id is None:
                continue
            target = avg_by_project.get(project_id)
            if target is None:
                target, _ = AverageDataSource.objects.get_or_create(
                    project_id=project_id,
                    name='AVG',
                    defaults={},
                )
                avg_by_project[project_id] = target
            Parameter.objects.filter(
                data_source_id=plain_id,
                star__project_id=project_id,
            ).update(data_source_id=target.pk)
        if not Parameter.objects.filter(data_source_id=plain_id).exists():
            plain.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0007_rename_dataset_valid_fit'),
        ('stars', '0004_remove_identifier_added_on_and_more'),
    ]

    operations = [
        migrations.RunPython(unify_avg_sources, migrations.RunPython.noop),
        migrations.DeleteModel(
            name='DataTable',
        ),
    ]
