# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-11 22:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mywiki', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='revision',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
            ],
        ),
    ]