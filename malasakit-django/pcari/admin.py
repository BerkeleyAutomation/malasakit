from django.contrib import admin

from .models import QualitativeQuestion, QuantitativeQuestion
from .models import CommentRating, Comment
from .models import QuantitativeQuestionRating, Respondent

admin.site.register(QualitativeQuestion)
admin.site.register(QuantitativeQuestion)
admin.site.register(QuantitativeQuestionRating)
admin.site.register(Respondent)

@admin.register(CommentRating)
class CommentRatingAdmin(admin.ModelAdmin):
    """
    Customizes admin change page function for CommentRatings
    """

    def get_message(self, obj):
        """
        A callable that returns the `message` attribute of the ForeignKey `comment`. 
        """
        return obj.comment.message

    # Empty responses (recorded as None) will be replaced by this placeholder
    empty_value_display = '-- empty response --'

    # Columns to display in the Comment change list page, in order from left to right
    list_display = ('respondent', 'get_message', 'score', 'timestamp')

    # By default first column listed in list_display is clickable; this makes `message` column clickable
    list_display_links = ('get_message',)

    # Specify which columns we want filtering capabilities for
    list_filter = ('timestamp', 'score')

    # Performance optimizer to limit database queries
    list_select_related = True

    # Sets default ordering to be most recent comment first
    ordering = ('-timestamp',)

    # Sets fields as readonly
    readonly_fields = ('respondent', 'score', 'comment')

    # Adds a "Save as New" button
    save_as = True

    # Enables search
    search_fields = ('score', 'comment__message')



@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """
    Customizes admin change page functionality for Comments
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
    search_fields = ('message', 'tag')

