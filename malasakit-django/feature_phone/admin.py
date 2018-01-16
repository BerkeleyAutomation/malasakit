""" Define how Django should present feature phone-specific models to administrators. """

from django import forms
from django.db import models
from django.contrib import admin

from pcari.admin import site
from feature_phone.models import Instructions, Question
from feature_phone.models import Response, Respondent


class RecordingAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.FileField: {
            'widget': forms.FileInput(attrs={'accept': 'audio/*'}),
        },
    }


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


@admin.register(Response, site=site)
class ResponseAdmin(RecordingAdmin):
    """ Admin for feature phone response model. """
    list_display = ('__unicode__', 'timestamp', 'respondent', 'url')
    list_filter = ('timestamp', )
    empty_value_display = '(Empty)'


@admin.register(Respondent, site=site)
class RespondentAdmin(RecordingAdmin):
    """ Admin for feature phone respondent model. """
    list_display = ('id', 'call_sid', 'age', 'gender', 'location', 'language')
    list_filter = ('language', )
    empty_value_display = '(Empty)'
