"""
This module defines how Django should render the admin panel.
"""

from django.contrib import admin

from .models import QualitativeQuestion, QuantitativeQuestion
from .models import CommentRating, Comment
from .models import QuantitativeQuestionRating, Respondent


admin.site.site_header = admin.site.site_title = 'Malasakit'


class ResponseAdmin(admin.ModelAdmin):
    """
    Abstract admin class for `CommentRatingAdmin`, `CommentAdmin`, and
    `QuantitativeQuestionRatingAdmin`.
    """
    # Empty responses (recorded as None) will be replaced by this placeholder
    empty_value_display = '-- Empty response --'

    # Performance optimizer to limit database queries
    list_select_related = True

    # Sets default ordering to be most recent comment first
    ordering = ('-timestamp',)

    # Adds a "Save as New" button
    save_as = True


@admin.register(CommentRating)
class CommentRatingAdmin(ResponseAdmin):
    """
    Customizes admin change page function for `CommentRating`s.
    """
    def get_comment_message(self, comment_rating):
        # pylint: disable=no-self-use
        return comment_rating.comment.message
    get_comment_message.short_description = 'Comment message'

    # Columns to display in the Comment change list page, in order from left to
    # right
    list_display = ('respondent', 'get_comment_message', 'score', 'timestamp',
                    'active')

    # By default first column listed in list_display is clickable; this makes
    # `message` column clickable
    list_display_links = ('get_comment_message',)

    # Specify which columns we want filtering capabilities for
    list_filter = ('timestamp', 'active')

    # Sets fields as readonly
    readonly_fields = ('respondent', 'score', 'comment')

    # Enables search
    search_fields = ('score', 'comment__message')


@admin.register(Comment)
class CommentAdmin(ResponseAdmin):
    """
    Customizes admin change page functionality for `Comment`s.
    """
    # Columns to display in the Comment change list page, in order from left to
    # right
    list_display = ('respondent', 'message', 'timestamp', 'language',
                    'flagged', 'tag', 'active')

    # By default first column listed in list_display is clickable; this makes
    # `message` column clickable
    list_display_links = ('message',)

    # Specify which columns we want filtering capabilities for
    list_filter = ('timestamp', 'language', 'flagged', 'tag', 'active')

    # Sets fields as readonly
    readonly_fields = ('respondent', 'question', 'language', 'message')

    # Enables search
    search_fields = ('message', 'tag')


@admin.register(QuantitativeQuestionRating)
class QuantitativeQuestionRatingAdmin(ResponseAdmin):
    """
    Customizes admin change page functionality for
    `QuantitativeQuestionRating`s.
    """
    def get_question_prompt(self, question_rating):
        # pylint: disable=no-self-use
        return question_rating.question.prompt
    get_question_prompt.short_description = 'Question prompt'

    # Columns to display in the Comment change list page, in order from left to
    # right
    list_display = ('respondent', 'get_question_prompt', 'timestamp', 'score',
                    'active')

    # By default first column listed in list_display is clickable; this makes
    # `message` column clickable
    list_display_links = ('get_question_prompt',)

    # Specify which columns we want filtering capabilities for
    list_filter = ('timestamp', 'active')

    # Sets fields as readonly
    readonly_fields = ('respondent', 'question', 'timestamp', 'score')

    # Enables search
    search_fields = ('question__prompt', 'score')


class QuestionAdmin(admin.ModelAdmin):
    """
    Abstract admin class for `QualitativeQuestionAdmin` and
    `QuantitativeQuestionAdmin`.
    """
    # Performance optimizer to limit database queries
    list_select_related = True

    # Adds a "Save as New" button
    save_as = True


@admin.register(QualitativeQuestion)
class QualitativeQuestionAdmin(QuestionAdmin):
    """
    Customizes admin change page functionality for `QualitativeQuestionAdmin`.
    """
    # Columns to display in the Comment change list page, in order from left to
    # right
    list_display = ('prompt', 'tag', 'active')

    # Specify which columns we want filtering capabilities for
    list_filter = ('prompt', 'tag', 'active')

    # Enables search
    search_fields = ('prompt', 'tag')


@admin.register(QuantitativeQuestion)
class QuantitativeQuestionAdmin(QuestionAdmin):
    """
    Customizes admin change page functionality for `QuantitativeQuestionAdmin`.
    """
    # Columns to display in the Comment change list page, in order from left to
    # right
    list_display = ('prompt', 'tag', 'active')

    # Specify which columns we want filtering capabilities for
    list_filter = ('tag', 'active')

    # Sets fields as readonly
    readonly_fields = ('prompt', 'tag')

    # Enables search
    search_fields = ('prompt', 'tag')


@admin.register(Respondent)
class RespondentAdmin(admin.ModelAdmin):
    """
    Customizes admin change page functionality for `RespondentAdmin`.
    """
    def comments_made(self, respondent):
        # pylint: disable=no-self-use
        comments = list(respondent.comments_made)
        return '(No comments)' if comments else ''.join(map(str, comments))

    # Empty responses (recorded as None) will be replaced by this placeholder
    empty_value_display = '(Empty)'

    # Performance optimizer to limit database queries
    list_select_related = True

    # Adds a "Save as New" button
    save_as = True

    # Columns to display in the Comment change list page, in order from left to
    # right
    list_display = ('comments_made', 'age', 'gender', 'location', 'language',
                    'submitted_personal_data', 'completed_survey',
                    'num_questions_rated', 'num_comments_rated', 'active')

    # Specify which columns we want filtering capabilities for
    list_filter = ('gender', 'language', 'submitted_personal_data',
                   'completed_survey', 'active')

    # Enables search
    search_fields = ('gender', 'location', 'language',
                     'submitted_personal_data', 'completed_survey',
                     'num_questions_rated', 'num_comments_rated')
