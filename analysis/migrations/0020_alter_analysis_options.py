from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0019_analysis_upload_path'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='analysis',
            options={
                'verbose_name_plural': 'analyses',
            },
        ),
    ]
