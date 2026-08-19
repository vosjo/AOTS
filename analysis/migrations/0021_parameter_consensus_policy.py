import django.db.models.deletion
import simple_history.models
from django.conf import settings
from django.db import migrations, models


def seed_default_consensus_policies(apps, schema_editor):
    Project = apps.get_model('stars', 'Project')
    Policy = apps.get_model('analysis', 'ParameterConsensusPolicy')
    for project in Project.objects.all():
        Policy.objects.get_or_create(
            project=project,
            name='*',
            component=0,
            defaults={
                'rule': 'weighted_average',
                'priority': 0,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ('stars', '0004_remove_identifier_added_on_and_more'),
        ('analysis', '0020_alter_analysis_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='parameter',
            name='consensus_provenance',
            field=models.CharField(blank=True, default='', max_length=200),
        ),
        migrations.AddField(
            model_name='parameter',
            name='consensus_rule',
            field=models.CharField(blank=True, default='', max_length=40),
        ),
        migrations.AddField(
            model_name='parameter',
            name='consensus_from',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='consensus_caches',
                to='analysis.parameter',
            ),
        ),
        migrations.CreateModel(
            name='ParameterConsensusPolicy',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('component', models.IntegerField(
                    choices=[(0, 'System'), (1, 'Primary'), (2, 'Secondary'), (5, 'Circumbinary Disk')],
                    default=0,
                )),
                ('rule', models.CharField(
                    choices=[
                        ('weighted_average', 'Weighted average'),
                        ('preferred_source', 'Preferred parameter source'),
                        ('preferred_analysis_category', 'Preferred analysis category'),
                        ('source_priority', 'Source priority list'),
                        ('latest', 'Latest measurement'),
                    ],
                    max_length=40,
                )),
                ('preferred_analysis_category', models.CharField(blank=True, default='', max_length=32)),
                ('source_priority', models.JSONField(blank=True, default=list)),
                ('fallback_rule', models.CharField(
                    blank=True,
                    choices=[
                        ('weighted_average', 'Weighted average'),
                        ('preferred_source', 'Preferred parameter source'),
                        ('preferred_analysis_category', 'Preferred analysis category'),
                        ('source_priority', 'Source priority list'),
                        ('latest', 'Latest measurement'),
                    ],
                    default='',
                    max_length=40,
                )),
                ('fallback_analysis_category', models.CharField(blank=True, default='', max_length=32)),
                ('priority', models.IntegerField(default=0)),
                ('fallback_preferred_source', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='consensus_fallback_policies',
                    to='analysis.parametersource',
                )),
                ('preferred_source', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='consensus_policies',
                    to='analysis.parametersource',
                )),
                ('project', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='consensus_policies',
                    to='stars.project',
                )),
            ],
            options={
                'ordering': ['name', 'component'],
            },
        ),
        migrations.AddConstraint(
            model_name='parameterconsensuspolicy',
            constraint=models.UniqueConstraint(
                fields=('project', 'name', 'component'),
                name='analysis_consensus_policy_unique',
            ),
        ),
        migrations.CreateModel(
            name='HistoricalParameterConsensusPolicy',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('component', models.IntegerField(
                    choices=[(0, 'System'), (1, 'Primary'), (2, 'Secondary'), (5, 'Circumbinary Disk')],
                    default=0,
                )),
                ('rule', models.CharField(
                    choices=[
                        ('weighted_average', 'Weighted average'),
                        ('preferred_source', 'Preferred parameter source'),
                        ('preferred_analysis_category', 'Preferred analysis category'),
                        ('source_priority', 'Source priority list'),
                        ('latest', 'Latest measurement'),
                    ],
                    max_length=40,
                )),
                ('preferred_analysis_category', models.CharField(blank=True, default='', max_length=32)),
                ('source_priority', models.JSONField(blank=True, default=list)),
                ('fallback_rule', models.CharField(
                    blank=True,
                    choices=[
                        ('weighted_average', 'Weighted average'),
                        ('preferred_source', 'Preferred parameter source'),
                        ('preferred_analysis_category', 'Preferred analysis category'),
                        ('source_priority', 'Source priority list'),
                        ('latest', 'Latest measurement'),
                    ],
                    default='',
                    max_length=40,
                )),
                ('fallback_analysis_category', models.CharField(blank=True, default='', max_length=32)),
                ('priority', models.IntegerField(default=0)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(
                    choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')],
                    max_length=1,
                )),
                ('fallback_preferred_source', models.ForeignKey(
                    blank=True,
                    db_constraint=False,
                    null=True,
                    on_delete=django.db.models.deletion.DO_NOTHING,
                    related_name='+',
                    to='analysis.parametersource',
                )),
                ('history_user', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='+',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('preferred_source', models.ForeignKey(
                    blank=True,
                    db_constraint=False,
                    null=True,
                    on_delete=django.db.models.deletion.DO_NOTHING,
                    related_name='+',
                    to='analysis.parametersource',
                )),
                ('project', models.ForeignKey(
                    blank=True,
                    db_constraint=False,
                    null=True,
                    on_delete=django.db.models.deletion.DO_NOTHING,
                    related_name='+',
                    to='stars.project',
                )),
            ],
            options={
                'verbose_name': 'historical parameter consensus policy',
                'verbose_name_plural': 'historical parameter consensus policies',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.RunPython(seed_default_consensus_policies, migrations.RunPython.noop),
    ]
