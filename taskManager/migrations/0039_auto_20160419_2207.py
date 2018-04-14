# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.utils.timezone import utc
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('taskManager', '0038_auto_20150921_2027'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='dob',
            field=models.CharField(max_length=8, default='00/00/00'),
        ),
        migrations.AlterField(
            model_name='project',
            name='due_date',
            field=models.DateTimeField(default=datetime.datetime(2016, 4, 26, 22, 7, 22, 761161, tzinfo=utc), verbose_name='date due'),
        ),
        migrations.AlterField(
            model_name='task',
            name='due_date',
            field=models.DateTimeField(default=datetime.datetime(2016, 4, 26, 22, 7, 22, 762688, tzinfo=utc), verbose_name='date due'),
        ),
    ]
