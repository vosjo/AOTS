from django.db import migrations, models


def migrate_method_to_category(apps, schema_editor):
    DataSet = apps.get_model('analysis', 'DataSet')
    Method = apps.get_model('analysis', 'Method')
    HistoricalDataSet = apps.get_model('analysis', 'HistoricalDataSet')

    from analysis.categories import resolve_category

    for dataset in DataSet.objects.select_related('method').iterator():
        if dataset.method_id:
            method = Method.objects.filter(pk=dataset.method_id).first()
            file_type = method.slug if method else ''
            category, source = resolve_category(file_type)
            dataset.file_type = file_type or ''
            dataset.category = category
            dataset.category_source = source
            dataset.save(update_fields=['file_type', 'category', 'category_source'])
        else:
            dataset.category = 'unknown'
            dataset.category_source = 'auto'
            dataset.save(update_fields=['category', 'category_source'])

    for row in HistoricalDataSet.objects.iterator():
        if row.method_id:
            method = Method.objects.filter(pk=row.method_id).first()
            file_type = method.slug if method else ''
            category, source = resolve_category(file_type)
            row.file_type = file_type or ''
            row.category = category
            row.category_source = source
            row.save(update_fields=['file_type', 'category', 'category_source'])
        elif not row.category:
            row.category = 'unknown'
            row.category_source = 'auto'
            row.save(update_fields=['category', 'category_source'])


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0004_parameter_star_index'),
    ]

    operations = [
        migrations.AddField(
            model_name='dataset',
            name='category',
            field=models.CharField(
                choices=[
                    ('rv_solution', 'RV solution'),
                    ('sed_fit', 'SED fit'),
                    ('lightcurve_fit', 'Light curve fit'),
                    ('spectral_fit', 'Spectral fit'),
                    ('grid_fit', 'Grid fit'),
                    ('cross_corr', 'Cross correlation'),
                    ('generic', 'Generic'),
                    ('unknown', 'Unknown'),
                ],
                default='unknown',
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name='dataset',
            name='category_source',
            field=models.CharField(
                choices=[('auto', 'Automatic'), ('user', 'User')],
                default='auto',
                max_length=8,
            ),
        ),
        migrations.AddField(
            model_name='dataset',
            name='file_type',
            field=models.CharField(blank=True, default='', max_length=32),
        ),
        migrations.AddField(
            model_name='historicaldataset',
            name='category',
            field=models.CharField(
                choices=[
                    ('rv_solution', 'RV solution'),
                    ('sed_fit', 'SED fit'),
                    ('lightcurve_fit', 'Light curve fit'),
                    ('spectral_fit', 'Spectral fit'),
                    ('grid_fit', 'Grid fit'),
                    ('cross_corr', 'Cross correlation'),
                    ('generic', 'Generic'),
                    ('unknown', 'Unknown'),
                ],
                default='unknown',
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name='historicaldataset',
            name='category_source',
            field=models.CharField(
                choices=[('auto', 'Automatic'), ('user', 'User')],
                default='auto',
                max_length=8,
            ),
        ),
        migrations.AddField(
            model_name='historicaldataset',
            name='file_type',
            field=models.CharField(blank=True, default='', max_length=32),
        ),
        migrations.RunPython(migrate_method_to_category, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='dataset',
            name='method',
        ),
        migrations.RemoveField(
            model_name='historicaldataset',
            name='method',
        ),
        migrations.DeleteModel(
            name='HistoricalMethod',
        ),
        migrations.DeleteModel(
            name='Method',
        ),
    ]
