from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0012_drop_analysis_parent_fk'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterModelOptions(
                    name='historicalanalysis',
                    options={
                        'get_latest_by': ('history_date', 'history_id'),
                        'ordering': ('-history_date', '-history_id'),
                        'verbose_name': 'historical analysis',
                        'verbose_name_plural': 'historical analyses',
                    },
                ),
                migrations.AlterModelTable(
                    name='averageparametersource',
                    table='analysis_averageparametersource',
                ),
            ],
        ),
    ]
