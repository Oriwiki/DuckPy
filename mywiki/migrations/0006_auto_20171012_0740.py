# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-11 22:40
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mywiki', '0005_auto_20171012_0735'),
    ]

    operations = [
        migrations.AddField(
            model_name='page',
            name='backlink',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='page',
            name='category',
            field=models.TextField(null=True),
        ),
    ]
