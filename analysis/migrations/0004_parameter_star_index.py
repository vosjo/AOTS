from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0003_remove_datasource_added_by_and_more'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='parameter',
            index=models.Index(fields=['star'], name='analysis_param_star_idx'),
        ),
    ]
