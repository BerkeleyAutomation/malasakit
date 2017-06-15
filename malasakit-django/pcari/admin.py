"""
This module defines how Django should render the admin panel.
"""
import csv

from django.contrib import admin
from django.http import HttpResponse
from django.utils.encoding import smart_str

from .models import QualitativeQuestion, QuantitativeQuestion
from .models import CommentRating, Comment
from .models import QuantitativeQuestionRating, Respondent


admin.site.site_header = admin.site.site_title = 'Malasakit'

def flag_comment(modeladmin, request, queryset):
    """
    Admin action that flags all selected unflagged comments

    Args:
        modeladmin: the current ModelAdmin the action is used in
        request: the HttpRequest object
        queryset: the set of objects selected by the user

    More info: https://docs.djangoproject.com/en/1.10/ref/contrib/admin/actions/
    """
    queryset.update(flagged=True)

flag_comment.short_description = "Flag selected comments"


def unflag_comment(modeladmin, request, queryset):
    """
    Admin action that unflags all selected unflagged comments

    Args:
        modeladmin: the current ModelAdmin the action is used in
        request: the HttpRequest object
        queryset: the set of objects selected by the user

    More info: https://docs.djangoproject.com/en/1.10/ref/contrib/admin/actions/
    """
    queryset.update(flagged=False)

unflag_comment.short_description = "Unflag selected comments"

def create_csv_response():
    """
    Create a response object to download CSV files

    Returns:
        an HttpResponse object for the CSV file to be downloaded
    """
    # instantiate the HttpResponse
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=malasakit_comment_data.csv'
    response.write(u'\ufeff'.encode('utf8'))

    return response


def create_comments_csv_writer(response):
    """
    Create a csv.writer object for dumping Comments

    Returns:
        a Writer object for dumping Comments into a CSV

    More info: 
        https://docs.python.org/2/library/csv.html
    """
    # instantiate the csv.writer object
    writer = csv.writer(response) # TODO: csv.excel might not be needed

    # write the column headers in the table
    writer.writerow([
        smart_str(u"Respondent"),
        smart_str(u"Question"),
        smart_str(u"Message"),
        smart_str(u"Language"),
        smart_str(u"Tag"),
        smart_str(u"Timestamp")
    ])

    return writer


def export_all_comments_csv(modeladmin, request, queryset):
    """
    Admin action that dumps all comments into a CSV file

    Args:
        modeladmin: the current ModelAdmin the action is used in
        request: the HttpRequest object
        queryset: the set of objects selected by the user

    Returns:
        an HttpResponse object containing the CSV file to be downloaded

    More info:
        https://docs.djangoproject.com/en/1.10/ref/contrib/admin/actions/
    """
    response = create_csv_response()

    writer = create_comments_csv_writer(response)

    # write the rows in the table
    comments = Comment.objects.all()
    for comment in comments:
        writer.writerow([
            smart_str(comment.respondent),
            smart_str(comment.question),
            smart_str(comment.message),
            smart_str(comment.language),
            smart_str(comment.tag),
            smart_str(comment.timestamp)
        ])

    return response

export_all_comments_csv.short_description = "Export all comments as a CSV (select one first)"


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

    # Columns to display in the Comment change list page, in order from left to
    # right
    list_display = ('respondent', 'get_comment_message', 'score', 'timestamp')

    # By default first column listed in list_display is clickable; this makes
    # `message` column clickable
    list_display_links = ('get_comment_message',)

    # Specify which columns we want filtering capabilities for
    list_filter = ('timestamp', 'score')

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
                    'flagged', 'tag')

    # By default first column listed in list_display is clickable; this makes
    # `message` column clickable
    list_display_links = ('message',)

    # Specify which columns we want filtering capabilities for
    list_filter = ('timestamp', 'language', 'flagged', 'tag')

    # Sets fields as readonly
    readonly_fields = ('respondent', 'question', 'language', 'message', 'timestamp')

    # Enables search
    search_fields = ('message', 'tag')

    # Actions that users can do on selected comments
    actions = (flag_comment, unflag_comment, export_all_comments_csv)


@admin.register(QuantitativeQuestionRating)
class QuantitativeQuestionRatingAdmin(ResponseAdmin):
    """
    Customizes admin change page functionality for
    `QuantitativeQuestionRating`s.
    """
    def get_question_prompt(self, question_rating):
        # pylint: disable=no-self-use
        return question_rating.question.prompt

    # Columns to display in the Comment change list page, in order from left to
    # right
    list_display = ('respondent', 'get_question_prompt', 'timestamp', 'score')

    # By default first column listed in list_display is clickable; this makes
    # `message` column clickable
    list_display_links = ('get_question_prompt',)

    # Specify which columns we want filtering capabilities for
    list_filter = ('timestamp', 'score')

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
    list_display = ('prompt', 'tag')

    # Specify which columns we want filtering capabilities for
    list_filter = ('tag', 'prompt')

    # Enables search
    search_fields = ('prompt', 'tag')


@admin.register(QuantitativeQuestion)
class QuantitativeQuestionAdmin(QuestionAdmin):
    """
    Customizes admin change page functionality for `QuantitativeQuestionAdmin`.
    """
    # Columns to display in the Comment change list page, in order from left to
    # right
    list_display = ('prompt', 'tag')

    # Specify which columns we want filtering capabilities for
    list_filter = ('tag',)

    # Sets fields as readonly
    readonly_fields = ('prompt', 'tag')

    # Enables search
    search_fields = ('prompt', 'tag')


@admin.register(Respondent)
class RespondentAdmin(admin.ModelAdmin):
    """
    Customizes admin change page functionality for `RespondentAdmin`.
    """
    def get_comments(self, respondent):
        # pylint: disable=no-self-use
        return list(respondent.comments_made)

    # Empty responses (recorded as None) will be replaced by this placeholder
    empty_value_display = '(Empty)'

    # Performance optimizer to limit database queries
    list_select_related = True

    # Adds a "Save as New" button
    save_as = True

    # Columns to display in the Comment change list page, in order from left to
    # right
    list_display = ('get_comments', 'age', 'gender', 'location', 'language',
                    'submitted_personal_data', 'completed_survey',
                    'num_questions_rated', 'num_comments_rated')

    # Specify which columns we want filtering capabilities for
    list_filter = ('gender', 'language', 'submitted_personal_data',
                   'completed_survey')

    # Enables search
    search_fields = ('gender', 'location', 'language',
                     'submitted_personal_data', 'completed_survey',
                     'num_questions_rated', 'num_comments_rated')
