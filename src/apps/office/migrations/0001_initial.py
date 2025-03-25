# Generated by Django 5.1.7 on 2025-03-25 14:58

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Letter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('letter_number', models.CharField(editable=False, max_length=20, unique=True)),
                ('letter_type', models.CharField(choices=[('to_officials', 'To Officials'), ('certificate_generation', 'Certificate Generation')], help_text='Type of Letter', max_length=30)),
                ('letter_content', models.JSONField(help_text='Letter content in JSON format')),
                ('issued_at', models.DateTimeField(auto_now_add=True)),
                ('issued_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='letters_issued', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Letter',
                'verbose_name_plural': 'Letters',
                'ordering': ['-issued_at'],
            },
        ),
    ]
