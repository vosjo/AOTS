from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('stars', '0004_remove_identifier_added_on_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='InteropImportBatch',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source', models.CharField(default='astra', max_length=32)),
                ('filename', models.CharField(blank=True, default='', max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(default='pending', max_length=32)),
                ('summary', models.JSONField(blank=True, default=dict)),
                ('warnings', models.JSONField(blank=True, default=list)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='interop_imports', to='stars.project')),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='InteropRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source', models.CharField(max_length=32)),
                ('external_id', models.CharField(max_length=128)),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('import_batch', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='records', to='interop.interopimportbatch')),
            ],
        ),
        migrations.AddIndex(
            model_name='interoprecord',
            index=models.Index(fields=['source', 'external_id'], name='interop_rec_source__8f0f0d_idx'),
        ),
        migrations.AddConstraint(
            model_name='interoprecord',
            constraint=models.UniqueConstraint(fields=('source', 'external_id', 'content_type'), name='interop_record_unique_external'),
        ),
    ]
