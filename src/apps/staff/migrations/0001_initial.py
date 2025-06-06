# Generated by Django 5.2 on 2025-05-22 21:25

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Staff',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('staff_type', models.CharField(choices=[('teaching', 'Teaching'), ('non-teaching', 'Non-Teaching')], max_length=20)),
                ('joining_date', models.DateField(help_text='Date when the staff joined')),
                ('leaving_date', models.DateField(blank=True, help_text='Date when the staff left', null=True)),
                ('leaving_reason', models.TextField(blank=True, help_text='Reason for leaving', null=True)),
                ('salary', models.DecimalField(decimal_places=2, help_text='Monthly salary', max_digits=12)),
                ('is_active', models.BooleanField(default=True, help_text='Is the staff member currently active?')),
                ('employment_history', models.JSONField(default=dict, help_text='History of employment in JSON format')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='staff_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Staff',
                'verbose_name_plural': 'Staff Members',
            },
        ),
        migrations.CreateModel(
            name='OtherStaff',
            fields=[
                ('staff', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='other_info', serialize=False, to='staff.staff')),
                ('position', models.CharField(help_text='Position (e.g., Accountant, Admin)', max_length=255)),
            ],
            options={
                'verbose_name': 'Other Staff',
                'verbose_name_plural': 'Other Staff',
            },
        ),
        migrations.CreateModel(
            name='Qualification',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('degree', models.CharField(help_text='Degree name (e.g., B.Ed, M.Sc.)', max_length=255)),
                ('institution', models.CharField(help_text='Institution name', max_length=255)),
                ('year_of_completion', models.PositiveIntegerField(help_text='Year of completion')),
                ('percentage', models.DecimalField(decimal_places=2, help_text='Percentage obtained', max_digits=5)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('staff', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='qualifications', to='staff.staff')),
            ],
            options={
                'verbose_name': 'Qualification',
                'verbose_name_plural': 'Qualifications',
            },
        ),
        migrations.CreateModel(
            name='TeachingStaff',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('national_teacher_id', models.CharField(help_text='National Teacher ID', max_length=50, unique=True)),
                ('state_teacher_id', models.CharField(help_text='State Teacher ID', max_length=50, unique=True)),
                ('teacher_level', models.CharField(choices=[('pre_primary', 'Pre-Primary'), ('primary', 'Primary'), ('jrt', 'Junior Secondary (JRT)'), ('senior_secondary', 'Senior Secondary')], max_length=20)),
                ('staff', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='teaching_info', to='staff.staff')),
            ],
            options={
                'verbose_name': 'Teaching Staff',
                'verbose_name_plural': 'Teaching Staff',
            },
        ),
        migrations.CreateModel(
            name='TeachingStaffSubject',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('subject', models.CharField(choices=[('mathematics', 'Mathematics'), ('science', 'Science'), ('english', 'English'), ('history', 'History'), ('geography', 'Geography'), ('computer_science', 'Computer Science')], help_text='Subject specialization', max_length=50)),
                ('preference', models.PositiveSmallIntegerField(help_text='Subject preference (1 for highest)')),
                ('staff', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subjects', to='staff.teachingstaff')),
            ],
            options={
                'verbose_name': 'Teaching Staff Subject',
                'verbose_name_plural': 'Teaching Staff Subjects',
                'ordering': ['preference'],
                'unique_together': {('staff', 'subject')},
            },
        ),
        migrations.CreateModel(
            name='Timetable',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('period', models.PositiveSmallIntegerField(choices=[(1, 'Period 1'), (2, 'Period 2'), (3, 'Period 3'), (4, 'Period 4'), (5, 'Period 5'), (6, 'Period 6'), (7, 'Period 7'), (8, 'Period 8')], help_text='Period number (1-8)')),
                ('class_name', models.CharField(choices=[('nursery', 'Nursery'), ('lkg', 'LKG'), ('ukg', 'UKG'), ('1', 'Class 1'), ('2', 'Class 2'), ('3', 'Class 3'), ('4', 'Class 4'), ('5', 'Class 5'), ('6', 'Class 6'), ('7', 'Class 7'), ('8', 'Class 8'), ('9', 'Class 9'), ('10', 'Class 10'), ('11', 'Class 11'), ('12', 'Class 12')], help_text='Class (Nursery-12)', max_length=10)),
                ('subject', models.CharField(help_text='Subject taught during this period', max_length=100)),
                ('time_start', models.TimeField(help_text='Start time of the period (e.g., 09:00 AM)')),
                ('time_end', models.TimeField(help_text='End time of the period (e.g., 09:40 AM)')),
                ('is_active', models.BooleanField(default=True, help_text='Is this timetable entry active?')),
                ('teacher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='timetable_entries', to='staff.teachingstaff')),
            ],
            options={
                'verbose_name': 'Timetable Entry',
                'verbose_name_plural': 'Timetable',
                'ordering': ['class_name', 'period'],
                'unique_together': {('period', 'class_name', 'time_start', 'teacher')},
            },
        ),
    ]
