# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-11 22:35
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mywiki', '0004_auto_20171012_0735'),
    ]

    operations = [
        migrations.AddField(
            model_name='revision',
            name='ip',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='mywiki.ip'),
        ),
        migrations.AlterField(
            model_name='revision',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
    ]