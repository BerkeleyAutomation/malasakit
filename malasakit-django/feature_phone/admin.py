""" Define how Django should present feature phone-specific models to administrators. """

import datetime
import os
import StringIO
import zipfile

from django import forms
from django.contrib import admin
from django.db import models
from django.http import HttpResponse

from pcari.admin import site
from feature_phone.models import Instructions, Question
from feature_phone.models import Response, Respondent


class RecordingAdmin(admin.ModelAdmin):
    """ Model admin that supports the storage of audio recordings. """
    formfield_overrides = {
        models.FileField: {
            'widget': forms.FileInput(attrs={'accept': 'audio/*'}),
        },
    }

    def get_file_fields(self, model):
        # pylint: disable=no-self-use
        return [field.name for field in model._meta.fields
                if isinstance(field, models.FileField)]

    def add_to_zip(self, zip_file, obj, fields):
        # pylint: disable=no-self-use
        for field_name in fields:
            field = getattr(obj, field_name)
            if hasattr(field, 'url'):
                destination = os.path.join(field_name, os.path.basename(field.path))
                zip_file.write(field.path, destination)

    def download_files(self, request, queryset):
        """ Prepare a ZIP file of all file fields for selected instances. """
        # pylint: disable=unused-argument
        file_fields = self.get_file_fields(queryset.model)
        zip_buffer = StringIO.StringIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            for obj in queryset:
                self.add_to_zip(zip_file, obj, file_fields)

        today = datetime.date.today().isoformat()
        model_name = queryset.model.__name__.lower()
        zip_filename = '{}-{}-recordings.zip'.format(today, model_name)
        response = HttpResponse(zip_buffer.getvalue(),
                                content_type='application/x-zip-compressed')
        response['Content-Disposition'] = 'attachment; filename={}'.format(zip_filename)
        return response

    download_files.short_description = 'Download a ZIP file of all recordings'


@admin.register(Instructions, Question, site=site)
class InstructionsAdmin(RecordingAdmin):
    """ Admin for feature phone instructions model, which includes questions. """
    def display_text(self, instructions):
        return instructions.text or self.get_empty_value_display()
    display_text.short_description = 'Text'

    def display_key(self, instructions):
        return instructions.key or self.get_empty_value_display()
    display_key.short_description = 'Tag'

    list_display = ('display_text', 'display_key', 'language', 'recording')
    list_filter = ('language', )
    search_fields = ('text', 'tag')
    empty_value_display = '(Empty)'
    actions = ('download_files', )


@admin.register(Response, site=site)
class ResponseAdmin(RecordingAdmin):
    """ Admin for feature phone response model. """
    list_display = ('__unicode__', 'timestamp', 'respondent', 'url')
    list_filter = ('timestamp', )
    empty_value_display = '(Empty)'
    actions = ('download_files', )


@admin.register(Respondent, site=site)
class RespondentAdmin(RecordingAdmin):
    """ Admin for feature phone respondent model. """
    list_display = ('id', 'call_sid', 'age', 'gender', 'location', 'language')
    list_filter = ('language', )
    empty_value_display = '(Empty)'
    actions = ('download_files', )
