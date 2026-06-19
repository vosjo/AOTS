from django.db import migrations


def seed_default_consensus_policies(apps, schema_editor):
    Project = apps.get_model('stars', 'Project')
    Policy = apps.get_model('analysis', 'ParameterConsensusPolicy')
    from analysis.services.consensus_defaults import seed_project_consensus_policies

    for project in Project.objects.all().iterator():
        seed_project_consensus_policies(project, policy_model=Policy)


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0021_parameter_consensus_policy'),
    ]

    operations = [
        migrations.RunPython(seed_default_consensus_policies, migrations.RunPython.noop),
    ]
