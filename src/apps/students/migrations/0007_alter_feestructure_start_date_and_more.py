# Generated by Django 5.1.7 on 2025-03-29 11:52

import datetime
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0006_rename_last_institution_previousinstitutiondetail_previous_institution'),
    ]

    operations = [
        migrations.AlterField(
            model_name='feestructure',
            name='start_date',
            field=models.DateField(default=datetime.date.today, help_text='Fee structure validity start date'),
        ),
        migrations.AlterField(
            model_name='studentadmission',
            name='fee_structure',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='student_admissions', to='students.feestructure'),
        ),
    ]
