# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-08-31 21:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pcari', '0028_auto_20160831_2041'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='accounted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='rating',
            name='accounted',
            field=models.BooleanField(default=False),
        ),
    ]