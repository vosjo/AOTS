from django.db import migrations, models


def flatten_average_parameter_source(apps, schema_editor):
    connection = schema_editor.connection
    avg_table = 'analysis_averageparametersource'
    src_table = 'analysis_parametersource'
    hist_table = 'analysis_historicalparametersource'

    with connection.cursor() as cursor:
        tables = connection.introspection.table_names(cursor)
    if avg_table not in tables:
        return

    if connection.vendor == 'postgresql':
        schema_editor.execute(
            f"""
            ALTER TABLE {schema_editor.quote_name(src_table)}
            ADD COLUMN IF NOT EXISTS kind varchar(16) NOT NULL DEFAULT 'catalog'
            """
        )
        if hist_table in tables:
            schema_editor.execute(
                f"""
                ALTER TABLE {schema_editor.quote_name(hist_table)}
                ADD COLUMN IF NOT EXISTS kind varchar(16) NOT NULL DEFAULT 'catalog'
                """
            )
        schema_editor.execute(
            f"""
            UPDATE {schema_editor.quote_name(src_table)} ps
            SET kind = 'average'
            FROM {schema_editor.quote_name(avg_table)} avg
            WHERE ps.id = avg.parametersource_ptr_id
            """
        )
        if hist_table in tables:
            schema_editor.execute(
                f"""
                UPDATE {schema_editor.quote_name(hist_table)} hps
                SET kind = 'average'
                WHERE hps.id IN (
                    SELECT parametersource_ptr_id FROM {schema_editor.quote_name(avg_table)}
                )
                """
            )
        schema_editor.execute(f'DROP TABLE {schema_editor.quote_name(avg_table)} CASCADE')
        return

    if connection.vendor == 'sqlite':
        with connection.cursor() as cursor:
            columns = {
                col.name
                for col in connection.introspection.get_table_description(cursor, src_table)
            }
        if 'kind' not in columns:
            schema_editor.execute(
                f"""
                ALTER TABLE "{src_table}"
                ADD COLUMN "kind" varchar(16) NOT NULL DEFAULT 'catalog'
                """
            )
        if hist_table in tables:
            with connection.cursor() as cursor:
                hist_columns = {
                    col.name
                    for col in connection.introspection.get_table_description(cursor, hist_table)
                }
            if 'kind' not in hist_columns:
                schema_editor.execute(
                    f"""
                    ALTER TABLE "{hist_table}"
                    ADD COLUMN "kind" varchar(16) NOT NULL DEFAULT 'catalog'
                    """
                )
        schema_editor.execute(
            f"""
            UPDATE "{src_table}"
            SET kind = 'average'
            WHERE id IN (SELECT parametersource_ptr_id FROM "{avg_table}")
            """
        )
        if hist_table in tables:
            schema_editor.execute(
                f"""
                UPDATE "{hist_table}"
                SET kind = 'average'
                WHERE id IN (SELECT parametersource_ptr_id FROM "{avg_table}")
                """
            )
        schema_editor.execute(f'DROP TABLE "{avg_table}"')


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0016_rename_analysis_pk_column'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(flatten_average_parameter_source, migrations.RunPython.noop),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='parametersource',
                    name='kind',
                    field=models.CharField(
                        choices=[
                            ('catalog', 'Catalog / manual'),
                            ('average', 'Project average container'),
                        ],
                        default='catalog',
                        max_length=16,
                    ),
                ),
                migrations.AddField(
                    model_name='historicalparametersource',
                    name='kind',
                    field=models.CharField(
                        choices=[
                            ('catalog', 'Catalog / manual'),
                            ('average', 'Project average container'),
                        ],
                        default='catalog',
                        max_length=16,
                    ),
                ),
                migrations.DeleteModel(
                    name='AverageParameterSource',
                ),
            ],
        ),
    ]
