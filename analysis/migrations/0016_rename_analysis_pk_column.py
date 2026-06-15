from django.db import migrations, models


def rename_analysis_pk_column(apps, schema_editor):
    connection = schema_editor.connection

    if connection.vendor == 'postgresql':
        schema_editor.execute(
            'ALTER TABLE analysis_analysis RENAME COLUMN datasource_ptr_id TO id'
        )
        schema_editor.execute(
            'ALTER TABLE analysis_historicalanalysis RENAME COLUMN datasource_ptr_id TO id'
        )
        return

    if connection.vendor == 'sqlite':
        schema_editor.execute(
            'ALTER TABLE analysis_analysis RENAME COLUMN datasource_ptr_id TO id'
        )
        schema_editor.execute(
            'ALTER TABLE analysis_historicalanalysis RENAME COLUMN datasource_ptr_id TO id'
        )


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0015_repair_historical_analysis_ids'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(rename_analysis_pk_column, migrations.RunPython.noop),
            ],
            state_operations=[
                migrations.AlterField(
                    model_name='analysis',
                    name='id',
                    field=models.AutoField(primary_key=True, serialize=False),
                ),
                migrations.AlterField(
                    model_name='historicalanalysis',
                    name='id',
                    field=models.IntegerField(blank=True, db_index=True),
                ),
            ],
        ),
    ]
