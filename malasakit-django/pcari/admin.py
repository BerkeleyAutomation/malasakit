from django.contrib import admin

from .models import QualitativeQuestion, QuantitativeQuestion, QuantitativeQuestionRating, Comment, CommentRating, Respondent

admin.site.register(QualitativeQuestion)
admin.site.register(QuantitativeQuestion)
admin.site.register(QuantitativeQuestionRating)
admin.site.register(CommentRating)
admin.site.register(Respondent)
admin.site.register(Comment)


