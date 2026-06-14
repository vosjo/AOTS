from django.db import migrations


def repair_historical_analysis_instance_ids(apps, schema_editor):
    Analysis = apps.get_model('analysis', 'Analysis')
    HistoricalAnalysis = apps.get_model('analysis', 'HistoricalAnalysis')

    for analysis in Analysis.objects.iterator():
        HistoricalAnalysis.objects.filter(
            datafile=analysis.datafile.name,
        ).update(id=analysis.pk)


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0014_alter_historicalanalysis_options'),
    ]

    operations = [
        migrations.RunPython(
            repair_historical_analysis_instance_ids,
            migrations.RunPython.noop,
        ),
    ]
