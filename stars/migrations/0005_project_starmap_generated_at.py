from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stars', '0004_remove_identifier_added_on_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='starmap_generated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
