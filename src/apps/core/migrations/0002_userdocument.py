# Generated by Django 5.1.7 on 2025-03-25 05:58

import apps.core.models
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file_path', models.FileField(upload_to=apps.core.models.user_document_upload_path)),
                ('document_name', models.CharField(max_length=100)),
                ('document_number', models.CharField(blank=True, max_length=100, null=True)),
                ('document_type', models.CharField(max_length=50)),
                ('version_s3', models.CharField(blank=True, max_length=255, null=True)),
                ('document_context', models.CharField(choices=[('student_admission', 'Student Admission'), ('staff_certification', 'Staff Certification'), ('previous_institution', 'Previous Institution'), ('rte', 'Right to Education (RTE)'), ('general', 'General')], max_length=50)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User Document',
                'verbose_name_plural': 'User Documents',
                'ordering': ['-uploaded_at'],
            },
        ),
    ]
