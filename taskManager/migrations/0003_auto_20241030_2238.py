# Generated by Django 3.2.21 on 2024-10-30 22:38

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('taskManager', '0002_auto_20230915_1957'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='due_date',
            field=models.DateTimeField(default=datetime.datetime(2024, 11, 6, 22, 38, 30, 943251, tzinfo=datetime.timezone.utc), verbose_name='date due'),
        ),
        migrations.AlterField(
            model_name='task',
            name='due_date',
            field=models.DateTimeField(default=datetime.datetime(2024, 11, 6, 22, 38, 30, 943700, tzinfo=datetime.timezone.utc), verbose_name='date due'),
        ),
    ]
