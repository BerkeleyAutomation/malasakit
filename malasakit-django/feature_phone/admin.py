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


class AdminViewMixin(admin.ModelAdmin):
    """
    Super class for admins to implement 'view' permissions.
    """
    def has_change_permission(self, request, obj=None):
        """
        This function is called to determine if a user can see feature phone
        objects in the admin panel. Will return true if the user has either
        "change" or "view" permissions on a model.
        """
        if admin.ModelAdmin.has_change_permission(self, request, obj):
            return True
        for perm in request.user.get_all_permissions():
            if 'view_' + self.model.__name__.lower() == perm.split('.')[1]:
                return True
        return False

    def get_readonly_fields(self, request, obj=None):
        """
        This function is called to determine which fields of feature phone
        objects cannot be edited. If a user only has "view" permissions, all
        fields are read-only. This does not prevent data download.
        """
        if admin.ModelAdmin.has_change_permission(self, request, obj):
            return self.readonly_fields
        for perm in request.user.get_all_permissions():
            if 'view_' + self.model.__name__.lower() == perm.split('.')[1]:
                return [field.name for field in self.opts.local_fields]
        return self.readonly_fields


class RecordingAdmin(AdminViewMixin):
    """ Model admin that supports the storage of audio recordings. """
    formfield_overrides = {
        models.FileField: {
            'widget': forms.FileInput(attrs={'accept': 'audio/*'}),
        },
    }

    def get_file_fields(self, model):
        """ Return a model's field names as a list of strings. """
        # pylint: disable=no-self-use
        return [field.name for field in model._meta.fields
                if isinstance(field, models.FileField)]

    def add_to_zip(self, zip_file, obj, fields):
        """
        Writes recording files of a model to zip folder sorted by subfolders
        named after each field of the object.

        Args:
            zip_file: a zipfile.ZipFile object where recordings will be written
                to.
            obj: an instance of a Response or Respondent object to save
                recordings from.
            fields: a list of strings where each element is a name of a field
                of obj.
        """
        # pylint: disable=no-self-use
        for field_name in fields:
            field = getattr(obj, field_name)
            if hasattr(field, 'url'):
                destination = os.path.join(field_name, os.path.basename(field.path))
                zip_file.write(field.path, destination)

    def download_files(self, request, queryset):
        """ Prepare a ZIP file of all file fields for selected instances.

        Args:
            queryset: a Django QuerySet of models selected for this action.
        """
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
