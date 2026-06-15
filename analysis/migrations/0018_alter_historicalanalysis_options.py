from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0017_flatten_average_parameter_source'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='historicalanalysis',
            options={
                'get_latest_by': ('history_date', 'history_id'),
                'ordering': ('-history_date', '-history_id'),
                'verbose_name': 'historical analysis',
                'verbose_name_plural': 'historical analyses',
            },
        ),
    ]
