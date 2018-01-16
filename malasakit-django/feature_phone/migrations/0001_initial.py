# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-09 17:57
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import feature_phone.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('pcari', '0053_auto_20170804_1930'),
    ]

    operations = [
        migrations.CreateModel(
            name='Instructions',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recording', models.FileField(upload_to=feature_phone.models.generate_recording_path)),
                ('text', models.TextField(blank=True, default='')),
                ('tag', models.CharField(blank=True, default='', max_length=256)),
                ('language', models.CharField(blank=True, choices=[(b'en', 'English'), (b'tl', 'Filipino')], default='', max_length=8, validators=[django.core.validators.RegexValidator('^(|en|tl)$')])),
            ],
            options={
                'verbose_name_plural': 'instructions',
            },
        ),
        migrations.CreateModel(
            name='Respondent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('age', models.FileField(blank=True, default=None, null=True, upload_to='respondent/age/')),
                ('gender', models.FileField(blank=True, default=True, null=True, upload_to='respondent/gender/')),
                ('location', models.FileField(blank=True, default=True, null=True, upload_to='respondent/location/')),
                ('language', models.CharField(blank=True, choices=[(b'en', 'English'), (b'tl', 'Filipino')], default='', max_length=8, validators=[django.core.validators.RegexValidator('^(|en|tl)$')])),
                ('related_object', models.OneToOneField(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='related_object', to='pcari.Respondent')),
            ],
        ),
        migrations.CreateModel(
            name='Response',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('related_object_id', models.PositiveIntegerField(blank=True, default=None, null=True)),
                ('recording', models.FileField(upload_to=feature_phone.models.generate_recording_path)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('prompt_id', models.PositiveIntegerField(blank=True, default=None, null=True)),
                ('prompt_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='contenttypes.ContentType')),
                ('related_object_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='contenttypes.ContentType')),
                ('respondent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='responses', to='feature_phone.Respondent')),
            ],
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('instructions_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='feature_phone.Instructions')),
                ('related_object_id', models.PositiveIntegerField(blank=True, default=None, null=True)),
                ('related_object_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
            bases=('feature_phone.instructions', models.Model),
        ),
        migrations.AlterUniqueTogether(
            name='response',
            unique_together=set([('prompt_type', 'prompt_id', 'respondent'), ('related_object_type', 'related_object_id')]),
        ),
    ]