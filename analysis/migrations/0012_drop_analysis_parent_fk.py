from django.db import migrations


def drop_analysis_parent_fk(apps, schema_editor):
    connection = schema_editor.connection
    table = 'analysis_analysis'

    if connection.vendor == 'postgresql':
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT conname
                FROM pg_constraint
                WHERE conrelid = 'analysis_analysis'::regclass
                  AND contype = 'f'
                  AND confrelid = 'analysis_parametersource'::regclass
                """
            )
            for (constraint_name,) in cursor.fetchall():
                schema_editor.execute(
                    f'ALTER TABLE {table} DROP CONSTRAINT {schema_editor.quote_name(constraint_name)}'
                )
        return

    if connection.vendor != 'sqlite':
        return

    schema_editor.execute(
        f"""
        CREATE TABLE "{table}_new" (
            "datasource_ptr_id" integer NOT NULL PRIMARY KEY,
            "datafile" varchar(100) NOT NULL,
            "fit" bool NOT NULL,
            "star_id" integer NULL REFERENCES "stars_star" ("id") DEFERRABLE INITIALLY DEFERRED,
            "category" varchar(32) NOT NULL,
            "category_source" varchar(8) NOT NULL,
            "file_type" varchar(32) NOT NULL,
            "name" varchar NOT NULL DEFAULT '',
            "note" varchar NOT NULL DEFAULT '',
            "reference" varchar NOT NULL DEFAULT '',
            "project_id" integer NOT NULL REFERENCES "stars_project" ("id") DEFERRABLE INITIALLY DEFERRED
        )
        """
    )
    schema_editor.execute(
        f"""
        INSERT INTO "{table}_new" (
            datasource_ptr_id, datafile, fit, star_id, category, category_source,
            file_type, name, note, reference, project_id
        )
        SELECT
            datasource_ptr_id, datafile, fit, star_id, category, category_source,
            file_type, name, note, reference, project_id
        FROM "{table}"
        """
    )
    schema_editor.execute(f'DROP TABLE "{table}"')
    schema_editor.execute(f'ALTER TABLE "{table}_new" RENAME TO "{table}"')
    schema_editor.execute(
        f'CREATE INDEX "analysis_analysis_star_id" ON "{table}" ("star_id")'
    )
    schema_editor.execute(
        f'CREATE INDEX "analysis_analysis_project_id" ON "{table}" ("project_id")'
    )


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0011_historical_analysis_fixup'),
    ]

    operations = [
        migrations.RunPython(drop_analysis_parent_fk, migrations.RunPython.noop),
    ]
