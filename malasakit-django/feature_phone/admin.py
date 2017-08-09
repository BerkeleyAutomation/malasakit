from django.contrib import admin

from pcari.admin import site
from feature_phone.models import Instructions, Question
from feature_phone.models import Response, Respondent


@admin.register(Instructions, site=site)
class InstructionsAdmin(admin.ModelAdmin):
    pass


@admin.register(Question, site=site)
class QuestionAdmin(admin.ModelAdmin):
    pass


@admin.register(Response, site=site)
class ResponseAdmin(admin.ModelAdmin):
    pass


@admin.register(Respondent, site=site)
class RespondentAdmin(admin.ModelAdmin):
    pass
