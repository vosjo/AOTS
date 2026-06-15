from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0018_alter_historicalanalysis_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='analysis',
            name='datafile',
            field=models.FileField(upload_to='analyses/'),
        ),
        migrations.AlterField(
            model_name='historicalanalysis',
            name='datafile',
            field=models.TextField(max_length=100),
        ),
    ]
