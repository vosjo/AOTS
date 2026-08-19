import django.db.models.deletion
from django.db import migrations, models


def add_analysis_standalone_columns(apps, schema_editor):
    connection = schema_editor.connection
    table = 'analysis_analysis'
    with connection.cursor() as cursor:
        existing = {
            col.name
            for col in connection.introspection.get_table_description(cursor, table)
        }

    if connection.vendor == 'postgresql':
        additions = [
            ('name', "text NOT NULL DEFAULT ''"),
            ('note', "text NOT NULL DEFAULT ''"),
            ('reference', "text NOT NULL DEFAULT ''"),
            ('project_id', 'integer NULL'),
        ]
    else:
        additions = [
            ('name', "varchar NOT NULL DEFAULT ''"),
            ('note', "varchar NOT NULL DEFAULT ''"),
            ('reference', "varchar NOT NULL DEFAULT ''"),
            ('project_id', 'integer NULL'),
        ]

    for column, definition in additions:
        if column not in existing:
            schema_editor.execute(
                f'ALTER TABLE {schema_editor.quote_name(table)} '
                f'ADD COLUMN {schema_editor.quote_name(column)} {definition}'
            )

    if 'project_id' not in existing and connection.vendor == 'postgresql':
        schema_editor.execute(
            'ALTER TABLE analysis_analysis '
            'ADD CONSTRAINT analysis_analysis_project_id_fk '
            'FOREIGN KEY (project_id) REFERENCES stars_project(id) '
            'DEFERRABLE INITIALLY DEFERRED'
        )


def copy_analysis_fields_and_migrate_parameters(apps, schema_editor):
    Analysis = apps.get_model('analysis', 'Analysis')
    DataSource = apps.get_model('analysis', 'DataSource')
    Parameter = apps.get_model('analysis', 'Parameter')

    analysis_ids = set()
    for analysis in Analysis.objects.all():
        parent_id = analysis.pk
        try:
            parent = DataSource.objects.get(pk=parent_id)
        except DataSource.DoesNotExist:
            continue
        analysis.name = parent.name
        analysis.note = parent.note
        analysis.reference = parent.reference
        analysis.project_id = parent.project_id
        analysis.save(update_fields=['name', 'note', 'reference', 'project_id'])
        analysis_ids.add(parent_id)

    for param in Parameter.objects.exclude(data_source_id__isnull=True).iterator():
        if param.data_source_id in analysis_ids:
            param.analysis_id = param.data_source_id
            param.parameter_source_id = None
        else:
            param.parameter_source_id = param.data_source_id
            param.analysis_id = None
        param.save(update_fields=['analysis_id', 'parameter_source_id'])


def delete_analysis_parent_datasource_rows(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return

    Analysis = apps.get_model('analysis', 'Analysis')
    DataSource = apps.get_model('analysis', 'DataSource')
    AverageDataSource = apps.get_model('analysis', 'AverageDataSource')

    analysis_ids = set(Analysis.objects.values_list('pk', flat=True))
    avg_parent_ids = set(
        AverageDataSource.objects.values_list('datasource_ptr_id', flat=True)
    )
    deletable = analysis_ids - avg_parent_ids
    if deletable:
        DataSource.objects.filter(pk__in=deletable).delete()


def drop_analysis_parent_fk(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    # Flush deferred FK triggers before DDL on the same table (PostgreSQL).
    schema_editor.execute('SET CONSTRAINTS ALL IMMEDIATE')
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT conname
            FROM pg_constraint
            WHERE conrelid = 'analysis_analysis'::regclass
              AND contype = 'f'
              AND confrelid = 'analysis_datasource'::regclass
            """
        )
        for (constraint_name,) in cursor.fetchall():
            schema_editor.execute(
                f'ALTER TABLE analysis_analysis DROP CONSTRAINT {schema_editor.quote_name(constraint_name)}'
            )


def rename_source_tables(apps, schema_editor):
    schema_editor.execute(
        'ALTER TABLE analysis_averagedatasource '
        'RENAME COLUMN datasource_ptr_id TO parametersource_ptr_id'
    )
    schema_editor.execute('ALTER TABLE analysis_datasource RENAME TO analysis_parametersource')
    schema_editor.execute(
        'ALTER TABLE analysis_averagedatasource RENAME TO analysis_averageparametersource'
    )
    schema_editor.execute(
        'ALTER TABLE analysis_historicaldatasource RENAME TO analysis_historicalparametersource'
    )


ANALYSIS_STANDALONE_FIELDS = [
    ('id', models.AutoField(db_column='datasource_ptr_id', primary_key=True, serialize=False)),
    ('name', models.TextField(default='')),
    ('note', models.TextField(default='')),
    ('reference', models.TextField(default='')),
    ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stars.project')),
    ('star', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='stars.star')),
    ('category', models.CharField(default='unknown', max_length=32)),
    ('category_source', models.CharField(default='auto', max_length=8)),
    ('file_type', models.CharField(blank=True, default='', max_length=32)),
    ('datafile', models.FileField(upload_to='datasets/')),
    ('fit', models.BooleanField(default=True)),
]


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ('analysis', '0009_rename_dataset_to_analysis'),
        ('stars', '0004_remove_identifier_added_on_and_more'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(add_analysis_standalone_columns, migrations.RunPython.noop),
            ],
            state_operations=[
                migrations.DeleteModel(name='Analysis'),
                migrations.CreateModel(
                    name='Analysis',
                    fields=ANALYSIS_STANDALONE_FIELDS,
                    options={'db_table': 'analysis_analysis'},
                ),
            ],
        ),
        migrations.AddField(
            model_name='parameter',
            name='analysis',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='parameter_set',
                to='analysis.analysis',
            ),
        ),
        migrations.AddField(
            model_name='parameter',
            name='parameter_source',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='analysis.datasource',
            ),
        ),
        migrations.RunPython(
            copy_analysis_fields_and_migrate_parameters,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name='analysis',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stars.project'),
        ),
        migrations.RemoveField(
            model_name='parameter',
            name='data_source',
        ),
        migrations.RunPython(drop_analysis_parent_fk, migrations.RunPython.noop),
        migrations.RunPython(
            delete_analysis_parent_datasource_rows,
            migrations.RunPython.noop,
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(rename_source_tables, migrations.RunPython.noop),
            ],
            state_operations=[
                migrations.DeleteModel(name='AverageDataSource'),
                migrations.RenameModel(
                    old_name='DataSource',
                    new_name='ParameterSource',
                ),
                migrations.CreateModel(
                    name='AverageParameterSource',
                    fields=[
                        (
                            'parametersource_ptr',
                            models.OneToOneField(
                                auto_created=True,
                                on_delete=django.db.models.deletion.CASCADE,
                                parent_link=True,
                                primary_key=True,
                                serialize=False,
                                to='analysis.parametersource',
                            ),
                        ),
                        ('datafile', models.FileField(null=True, upload_to='datatables/')),
                    ],
                    options={'db_table': 'analysis_averagedatasource'},
                ),
                migrations.RenameModel(
                    old_name='HistoricalDataSource',
                    new_name='HistoricalParameterSource',
                ),
            ],
        ),
        migrations.AlterField(
            model_name='parameter',
            name='parameter_source',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='analysis.parametersource',
            ),
        ),
    ]
