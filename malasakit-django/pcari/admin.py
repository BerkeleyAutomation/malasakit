from django.contrib import admin

from .models import QualitativeQuestion, QuantitativeQuestion, QuantitativeQuestionRating, CommentRating, Comment, Respondent

admin.site.register(QualitativeQuestion)
admin.site.register(QuantitativeQuestion)
admin.site.register(QuantitativeQuestionRating)
admin.site.register(CommentRating)
admin.site.register(Comment)
admin.site.register(Respondent)
