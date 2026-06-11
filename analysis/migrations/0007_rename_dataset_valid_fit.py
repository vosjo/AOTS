from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0006_rv_curve_remove_grid_fit'),
    ]

    operations = [
        migrations.RenameField(
            model_name='dataset',
            old_name='valid',
            new_name='fit',
        ),
        migrations.RenameField(
            model_name='historicaldataset',
            old_name='valid',
            new_name='fit',
        ),
    ]
