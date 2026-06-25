from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_user_api_key_user_api_secret_user_profile_picture'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='api_key',
            field=models.CharField(blank=True, max_length=120, null=True, unique=True),
        ),
    ]
