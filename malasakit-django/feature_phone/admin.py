"""Django admin page for managing feature phone recordings, instructions,
questions and responses."""
import os
import StringIO
import zipfile

from django import forms
from django.conf import settings
from django.contrib import admin
from django.db import models
from django.http import HttpResponse
from django.utils.html import format_html

from pcari.admin import site
from feature_phone.models import Instructions, Question
from feature_phone.models import Response, Respondent


class RecordingAdmin(admin.ModelAdmin):
    """Superclass for admin functionality that involve recordings."""
    formfield_overrides = {
        models.FileField: {
            'widget': forms.FileInput(attrs={'accept': 'audio/*'}),
        },
    }


    # pylint: disable=unused-argument, no-self-use
    def download_list_action(self, request, queryset):
        """Function called when user attempts to download a list of
        recordings.

        Args:
            request: unused
            queryset: list of objects to be downloaded
        """


        def zip_file(z_file, obj, file_field, folder=False):
            """Write obj to a zip file if the obj has a file field.

            Args:
                z_file: zip file to write into
                obj: object to put into the zip file
                file_field: name of field of the obj that has a recording
                folder: true/false on whether to put obj in sub folder

            """

            if hasattr(obj, file_field) and hasattr(getattr(obj, file_field),
                                                    'url'):
                fpath = str(os.path.join(os.path.dirname(settings.MEDIA_ROOT),
                                         str(getattr(obj, file_field).url)[1:]))
                base = os.path.basename(fpath)
                if folder:
                    base = file_field + '/' + base
                print fpath, base
                z_file.write(fpath, base)


        zip_filename = 'audio.zip'
        str_io = StringIO.StringIO()
        with zipfile.ZipFile(str_io, 'w') as z_file:
            for obj in queryset:
                zip_file(z_file, obj, 'recording')
                zip_file(z_file, obj, 'age', folder=True)
                zip_file(z_file, obj, 'gender', folder=True)
                zip_file(z_file, obj, 'location', folder=True)

        response = HttpResponse(str_io.getvalue(), content_type=
                                'application/x-zip-compressed')
        response['Content-Disposition'] = 'attachment; filename={}'.format(
            zip_filename)
        return response
    download_list_action.short_description = 'Download selected mp3 files'


    # pylint: disable=no-self-use
    def download_button(self, obj):
        return format_html('<a class="button" href="{}"download>Download</a>'
                           .format(obj.recording.url))
    download_button.short_description = 'mp3 file'



@admin.register(Instructions, site=site)
class InstructionsAdmin(RecordingAdmin):
    """Admin for instructions."""
    def display_text(self, instructions):
        return instructions.text or self.get_empty_value_display()
    display_text.short_description = 'Text'
    def display_tag(self, instructions):
        return instructions.tag or self.get_empty_value_display()
    display_tag.short_description = 'Tag'
    list_display = ('display_text', 'display_tag', 'language', 'download_button')
    list_filter = ('language', )
    search_fields = ('text', 'tag')
    empty_value_display = '(Empty)'
    actions = ('download_list_action',)


# class QuestionInline(GenericTabularInline):
#     model = Question


@admin.register(Question, site=site)
class QuestionAdmin(InstructionsAdmin):
    list_display = ('download_button',)
    actions = ('download_list_action',)


@admin.register(Response, site=site)
class ResponseAdmin(RecordingAdmin):
    """Admin for responses."""
    # pylint: disable=no-self-use
    def display_response(self, response):
        return response


    list_display = ('display_response', 'download_button')
    actions = ('download_list_action',)


@admin.register(Respondent, site=site)
class RespondentAdmin(RecordingAdmin):
    actions = ('download_list_action',)
