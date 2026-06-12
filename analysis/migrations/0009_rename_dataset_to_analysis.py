from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0008_unify_avg_remove_datatable'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='DataSet',
            new_name='Analysis',
        ),
        migrations.RenameModel(
            old_name='HistoricalDataSet',
            new_name='HistoricalAnalysis',
        ),
    ]
