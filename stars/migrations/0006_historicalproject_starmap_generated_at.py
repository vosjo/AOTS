from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stars', '0005_project_starmap_generated_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalproject',
            name='starmap_generated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
