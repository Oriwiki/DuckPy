# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-11 22:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mywiki', '0006_auto_20171012_0740'),
    ]

    operations = [
        migrations.AlterField(
            model_name='page',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
    ]