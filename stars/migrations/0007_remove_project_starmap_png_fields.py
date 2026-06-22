from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stars', '0006_historicalproject_starmap_generated_at'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='historicalproject',
            name='full_starmap',
        ),
        migrations.RemoveField(
            model_name='historicalproject',
            name='preview_starmap',
        ),
        migrations.RemoveField(
            model_name='historicalproject',
            name='starmap_generated_at',
        ),
        migrations.RemoveField(
            model_name='project',
            name='full_starmap',
        ),
        migrations.RemoveField(
            model_name='project',
            name='preview_starmap',
        ),
        migrations.RemoveField(
            model_name='project',
            name='starmap_generated_at',
        ),
    ]
