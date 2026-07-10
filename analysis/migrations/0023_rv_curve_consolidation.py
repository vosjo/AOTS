from django.db import migrations


def migrate_rv_solution_to_rv_curve(apps, schema_editor):
    Analysis = apps.get_model('analysis', 'Analysis')
    HistoricalAnalysis = apps.get_model('analysis', 'HistoricalAnalysis')
    Policy = apps.get_model('analysis', 'ParameterConsensusPolicy')
    HistoricalPolicy = apps.get_model('analysis', 'HistoricalParameterConsensusPolicy')

    Analysis.objects.filter(category='rv_solution').update(category='rv_curve')
    HistoricalAnalysis.objects.filter(category='rv_solution').update(category='rv_curve')

    for field in ('preferred_analysis_category', 'fallback_analysis_category'):
        Policy.objects.filter(**{field: 'rv_solution'}).update(**{field: 'rv_curve'})
        HistoricalPolicy.objects.filter(**{field: 'rv_solution'}).update(**{field: 'rv_curve'})


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0022_seed_consensus_policy_defaults'),
    ]

    operations = [
        migrations.RunPython(migrate_rv_solution_to_rv_curve, migrations.RunPython.noop),
    ]
