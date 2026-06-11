from django.db import migrations, models


CATEGORY_CHOICES = [
    ('rv_solution', 'RV solution'),
    ('rv_curve', 'RV curve'),
    ('sed_fit', 'SED fit'),
    ('lightcurve_fit', 'Light curve fit'),
    ('spectral_fit', 'Spectral fit'),
    ('cross_corr', 'Cross correlation'),
    ('generic', 'Generic'),
    ('unknown', 'Unknown'),
]


def migrate_grid_fit_to_generic(apps, schema_editor):
    for model_name in ('DataSet', 'HistoricalDataSet'):
        Model = apps.get_model('analysis', model_name)
        Model.objects.filter(category='grid_fit').update(category='generic')


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0005_dataset_categories_remove_method'),
    ]

    operations = [
        migrations.RunPython(migrate_grid_fit_to_generic, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='dataset',
            name='category',
            field=models.CharField(
                choices=CATEGORY_CHOICES,
                default='unknown',
                max_length=32,
            ),
        ),
        migrations.AlterField(
            model_name='historicaldataset',
            name='category',
            field=models.CharField(
                choices=CATEGORY_CHOICES,
                default='unknown',
                max_length=32,
            ),
        ),
    ]
