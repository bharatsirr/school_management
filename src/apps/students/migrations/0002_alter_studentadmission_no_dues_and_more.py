# Generated by Django 5.1.7 on 2025-03-25 14:04

import apps.students.models
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentadmission',
            name='no_dues',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='studentadmission',
            name='session',
            field=models.CharField(default=apps.students.models.StudentAdmission.generate_session, help_text='e.g., 2023-2024 leave blank to set to current session', max_length=9),
        ),
        migrations.CreateModel(
            name='PreviousInstitutionDetail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_institution', models.CharField(help_text='Name of the last attended institution', max_length=255)),
                ('score', models.DecimalField(decimal_places=2, help_text='Obtained marks', max_digits=7)),
                ('mm', models.DecimalField(decimal_places=2, help_text='Maximum marks', max_digits=7)),
                ('percent', models.DecimalField(blank=True, decimal_places=2, help_text='Percentage (auto-calculated)', max_digits=5, null=True)),
                ('rte', models.BooleanField(default=False, help_text='Right to Education (RTE) beneficiary?')),
                ('student', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='previous_institution', to='students.student')),
            ],
        ),
    ]
