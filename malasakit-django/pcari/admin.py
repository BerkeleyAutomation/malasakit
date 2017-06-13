from django.contrib import admin

from .models import QualitativeQuestion, QuantitativeQuestion, QuantitativeQuestionRating, CommentRating, Comment, Respondent

admin.site.register(QualitativeQuestion)
admin.site.register(QuantitativeQuestion)
admin.site.register(QuantitativeQuestionRating)
admin.site.register(CommentRating)

class CommentAdmin(admin.ModelAdmin):
    """
    Customizes admin page functionality for Comment
    """
    # Empty responses (recorded as None) will be replaced by this placeholder
    empty_value_display = '-- empty response --'

    # Columns to display in the Comment change list page, in order from left to right 
    list_display = ('respondent', 'message', 'timestamp', 'language', 'flagged', 'tag')

    # By default first column listed in list_display is clickable; this makes `message` column clickable
    list_display_links = ('message',)

    # Specify which columns we want filtering capabilities for
    list_filter = ('timestamp', 'language', 'flagged', 'tag')

    # Performance optimizer to limit database queries
    list_select_related = True

    # Sets default ordering to be most recent comment first
    ordering = ('-timestamp',)

    # Sets fields as readonly
    readonly_fields = ('respondent', 'question', 'language', 'message')

    # Adds a "Save as New" button
    save_as = True

    # Enables search
    search_fields = ('respondent', 'message', 'tag')


    # list_filter = ('timestamp', )

admin.site.register(Comment, CommentAdmin)

admin.site.register(Respondent)
