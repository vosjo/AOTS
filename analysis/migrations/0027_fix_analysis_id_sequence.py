"""Ensure analysis_analysis.id has a PostgreSQL sequence after the MTI → standalone split.

Migrations 0010–0016 renamed ``datasource_ptr_id`` → ``id`` but never attached a
SERIAL/identity default. New INSERTs then send ``id=NULL`` and fail with
IntegrityError on PostgreSQL.
"""

from django.db import migrations

SEQUENCE = 'analysis_analysis_id_seq'


def fix_analysis_id_sequence(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(f'CREATE SEQUENCE IF NOT EXISTS {SEQUENCE}')
        cursor.execute(
            """
            SELECT setval(
                %s,
                GREATEST(COALESCE((SELECT MAX(id) FROM analysis_analysis), 1), 1),
                true
            )
            """,
            [SEQUENCE],
        )
        cursor.execute(
            f'ALTER TABLE analysis_analysis '
            f"ALTER COLUMN id SET DEFAULT nextval('{SEQUENCE}')"
        )
        cursor.execute(
            f'ALTER SEQUENCE {SEQUENCE} OWNED BY analysis_analysis.id'
        )


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0026_multi_fit_rollout'),
    ]

    operations = [
        migrations.RunPython(fix_analysis_id_sequence, migrations.RunPython.noop),
    ]
