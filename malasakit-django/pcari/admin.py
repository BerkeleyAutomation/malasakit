from django.contrib import admin

from .models import QualitativeQuestion, QuantitativeQuestion, QuantitativeQuestionRating, CommentRating, Comment, Respondent

admin.site.register(QualitativeQuestion)
admin.site.register(QuantitativeQuestion)
admin.site.register(QuantitativeQuestionRating)
admin.site.register(CommentRating)

class CommentAdmin(admin.ModelAdmin):
    """Customizes admin page functionality for Comment"""
    # Empty responses (recorded as None) will be replaced by this placeholder
    empty_value_display = '-- empty response --' 

    # Columns to display in the Comment change list page. First column listed is clickable. 
    list_display = ('message', 'timestamp', 'language', 'flagged', 'tag')

admin.site.register(Comment, CommentAdmin)

admin.site.register(Respondent)
