from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('observations', '0012_remove_lightcurve_added_by_and_more'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='spectrum',
            index=models.Index(fields=['project', 'hjd'], name='obs_spec_proj_hjd_idx'),
        ),
        migrations.AddIndex(
            model_name='spectrum',
            index=models.Index(fields=['star'], name='obs_spec_star_idx'),
        ),
        migrations.AddIndex(
            model_name='lightcurve',
            index=models.Index(fields=['project', 'hjd'], name='obs_lc_proj_hjd_idx'),
        ),
        migrations.AddIndex(
            model_name='specfile',
            index=models.Index(fields=['project', 'hjd'], name='obs_spf_proj_hjd_idx'),
        ),
    ]
