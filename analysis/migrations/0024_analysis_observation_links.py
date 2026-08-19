import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('observations', '0013_list_query_indexes'),
        ('analysis', '0023_rv_curve_consolidation'),
    ]

    operations = [
        migrations.AddField(
            model_name='analysis',
            name='is_best_fit',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='analysis',
            name='lightcurve',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='analyses',
                to='observations.lightcurve',
            ),
        ),
        migrations.AddField(
            model_name='analysis',
            name='spectrum',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='analyses',
                to='observations.spectrum',
            ),
        ),
        migrations.AddField(
            model_name='historicalanalysis',
            name='is_best_fit',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='historicalanalysis',
            name='lightcurve',
            field=models.ForeignKey(
                blank=True,
                db_constraint=False,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name='+',
                to='observations.lightcurve',
            ),
        ),
        migrations.AddField(
            model_name='historicalanalysis',
            name='spectrum',
            field=models.ForeignKey(
                blank=True,
                db_constraint=False,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name='+',
                to='observations.spectrum',
            ),
        ),
        migrations.AddConstraint(
            model_name='analysis',
            constraint=models.CheckConstraint(
                condition=~models.Q(spectrum__isnull=False, lightcurve__isnull=False),
                name='analysis_single_observation_parent',
            ),
        ),
    ]
