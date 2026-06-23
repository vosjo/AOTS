from django.db import migrations, models


def fix_historical_analysis_table(apps, schema_editor):
    connection = schema_editor.connection
    table = 'analysis_historicalanalysis'
    with connection.cursor() as cursor:
        columns = {
            col.name
            for col in connection.introspection.get_table_description(cursor, table)
        }

    if connection.vendor == 'sqlite':
        if 'id' not in columns:
            return
        schema_editor.execute(
            f"""
            CREATE TABLE "{table}_new" (
                "datasource_ptr_id" integer NULL,
                "name" text NOT NULL,
                "note" text NOT NULL,
                "reference" text NOT NULL,
                "datafile" text NOT NULL,
                "fit" bool NOT NULL,
                "history_id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                "history_date" datetime NOT NULL,
                "history_change_reason" varchar(100) NULL,
                "history_type" varchar(1) NOT NULL,
                "history_user_id" integer NULL REFERENCES "users_user" ("id") DEFERRABLE INITIALLY DEFERRED,
                "project_id" integer NULL,
                "star_id" integer NULL,
                "category" varchar(32) NOT NULL,
                "category_source" varchar(8) NOT NULL,
                "file_type" varchar(32) NOT NULL
            )
            """
        )
        schema_editor.execute(
            f"""
            INSERT INTO "{table}_new" (
                datasource_ptr_id, name, note, reference, datafile, fit,
                history_id, history_date, history_change_reason, history_type,
                history_user_id, project_id, star_id, category, category_source, file_type
            )
            SELECT
                COALESCE("datasource_ptr_id", "id"),
                name, note, reference, datafile, fit,
                history_id, history_date, history_change_reason, history_type,
                history_user_id, project_id, star_id, category, category_source, file_type
            FROM "{table}"
            """
        )
        schema_editor.execute(f'DROP TABLE "{table}"')
        schema_editor.execute(f'ALTER TABLE "{table}_new" RENAME TO "{table}"')
        schema_editor.execute(
            f'CREATE INDEX "analysis_historicalanalysis_datasource_ptr_id" ON "{table}" ("datasource_ptr_id")'
        )
        schema_editor.execute(
            f'CREATE INDEX "analysis_historicalanalysis_history_date" ON "{table}" ("history_date")'
        )
        schema_editor.execute(
            f'CREATE INDEX "analysis_historicalanalysis_history_user_id" ON "{table}" ("history_user_id")'
        )
        schema_editor.execute(
            f'CREATE INDEX "analysis_historicalanalysis_project_id" ON "{table}" ("project_id")'
        )
        schema_editor.execute(
            f'CREATE INDEX "analysis_historicalanalysis_star_id" ON "{table}" ("star_id")'
        )
        return

    if connection.vendor == 'postgresql':
        schema_editor.execute(
            'DROP INDEX IF EXISTS analysis_historicaldataset_id_0e6ce607'
        )
        if 'id' in columns and 'datasource_ptr_id' in columns:
            schema_editor.execute(
                f'UPDATE {table} '
                'SET datasource_ptr_id = id '
                'WHERE datasource_ptr_id IS NULL'
            )
            schema_editor.execute(f'ALTER TABLE {table} DROP COLUMN id')
        elif 'id' in columns:
            schema_editor.execute(
                f'ALTER TABLE {table} RENAME COLUMN id TO datasource_ptr_id'
            )


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0010_parameter_source_refactor'),
    ]

    operations = [
        migrations.RunPython(fix_historical_analysis_table, migrations.RunPython.noop),
        migrations.AlterModelOptions(
            name='historicalanalysis',
            options={
                'get_latest_by': ('history_date', 'history_id'),
                'ordering': ('-history_date', '-history_id'),
                'verbose_name': 'historical analysis',
                'verbose_name_plural': 'historical analyses',
            },
        ),
        migrations.AlterModelOptions(
            name='historicalparametersource',
            options={
                'get_latest_by': ('history_date', 'history_id'),
                'ordering': ('-history_date', '-history_id'),
                'verbose_name': 'historical parameter source',
                'verbose_name_plural': 'historical parameter sources',
            },
        ),
        migrations.RemoveIndex(
            model_name='parameter',
            name='analysis_param_star_idx',
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.RemoveField(
                    model_name='historicalanalysis',
                    name='datasource_ptr',
                ),
                migrations.AlterField(
                    model_name='historicalanalysis',
                    name='id',
                    field=models.IntegerField(
                        blank=True,
                        db_column='datasource_ptr_id',
                        db_index=True,
                    ),
                ),
            ],
        ),
        migrations.AlterField(
            model_name='analysis',
            name='category',
            field=models.CharField(
                choices=[
                    ('rv_solution', 'RV solution'),
                    ('rv_curve', 'RV curve'),
                    ('sed_fit', 'SED fit'),
                    ('lightcurve_fit', 'Light curve fit'),
                    ('spectral_fit', 'Spectral fit'),
                    ('cross_corr', 'Cross correlation'),
                    ('generic', 'Generic'),
                    ('unknown', 'Unknown'),
                ],
                default='unknown',
                max_length=32,
            ),
        ),
        migrations.AlterField(
            model_name='analysis',
            name='category_source',
            field=models.CharField(
                choices=[('auto', 'Automatic'), ('user', 'User')],
                default='auto',
                max_length=8,
            ),
        ),
    ]
