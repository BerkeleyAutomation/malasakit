# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-14 19:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pcari', '0054_auto_20170811_2154'),
    ]

    operations = [
        migrations.AddField(
            model_name='respondent',
            name='uuid',
            field=models.UUIDField(blank=True, default=None, editable=False, null=True, unique=True),
        ),
    ]
