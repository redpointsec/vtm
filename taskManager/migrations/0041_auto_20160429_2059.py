# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('taskManager', '0040_auto_20160420_1859'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='due_date',
            field=models.DateTimeField(default=datetime.datetime(2016, 5, 6, 20, 59, 46, 374715, tzinfo=utc), verbose_name='date due'),
        ),
        migrations.AlterField(
            model_name='task',
            name='due_date',
            field=models.DateTimeField(default=datetime.datetime(2016, 5, 6, 20, 59, 46, 376575, tzinfo=utc), verbose_name='date due'),
        ),
    ]
