# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-18 12:11
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('mywiki', '0002_revision_file'),
    ]

    operations = [
        migrations.CreateModel(
            name='Block',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('blockDate', models.DateTimeField(auto_now_add=True)),
                ('period', models.DateField()),
                ('comment', models.CharField(max_length=255, null=True)),
                ('admin', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='admin', to=settings.AUTH_USER_MODEL)),
                ('blocked_ip', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='mywiki.Ip')),
                ('blocked_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='blocked_user', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
