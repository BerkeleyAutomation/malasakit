from django import forms
from django.db import models
from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline

from pcari.admin import site
from feature_phone.models import Instructions, Question
from feature_phone.models import Response, Respondent


class RecordingAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.FileField: {
            'widget': forms.FileInput(attrs={'accept': 'audio/*'}),
        },
    }


@admin.register(Instructions, site=site)
class InstructionsAdmin(RecordingAdmin):
    def display_text(self, instructions):
        return instructions.text or self.get_empty_value_display()
    display_text.short_description = 'Text'
    def display_tag(self, instructions):
        return instructions.tag or self.get_empty_value_display()
    display_tag.short_description = 'Tag'
    list_display = ('display_text', 'display_tag', 'language', 'recording')
    list_filter = ('language', )
    search_fields = ('text', 'tag')
    empty_value_display = '(Empty)'


# class QuestionInline(GenericTabularInline):
#     model = Question


@admin.register(Question, site=site)
class QuestionAdmin(InstructionsAdmin):
    pass  # inlines = [QuestionInline]


@admin.register(Response, site=site)
class ResponseAdmin(RecordingAdmin):
    pass


@admin.register(Respondent, site=site)
class RespondentAdmin(RecordingAdmin):
    pass
