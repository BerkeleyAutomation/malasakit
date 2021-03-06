# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-27 08:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feature_phone', '0002_auto_20170809_1854'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='instructions',
            name='tag',
        ),
        migrations.AddField(
            model_name='instructions',
            name='key',
            field=models.SlugField(default=None, unique=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='respondent',
            name='gender',
            field=models.FileField(blank=True, default=None, null=True, upload_to='respondent/gender/'),
        ),
        migrations.AlterField(
            model_name='respondent',
            name='location',
            field=models.FileField(blank=True, default=None, null=True, upload_to='respondent/location/'),
        ),
    ]
