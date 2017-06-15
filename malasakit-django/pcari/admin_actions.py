"""
This module contains all the custom actions for the admin change pages.
"""

import csv

from django.http import HttpResponse
from django.utils.encoding import smart_str

from .models import QualitativeQuestion, QuantitativeQuestion
from .models import CommentRating, Comment
from .models import QuantitativeQuestionRating, Respondent


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
    Helper function for export_all_comments_csv, export_selected_comments_csv, 
    export_all_commentratings_csv, export_selected_commentratings_csv,
    export_all_quantitativequestionratings_csv, export_selected_quantitativequestionratings_csv

    Returns:
        an HttpResponse object for the CSV file to be downloaded
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=malasakit_comment_data.csv'
    response.write(u'\ufeff'.encode('utf8'))

    return response


def create_comments_csv_writer(response):
    """
    Create a csv.writer object for dumping Comments
    Helper function for export_all_comments_csv, export_selected_comments_csv

    Returns:
        a Writer object for dumping Comments into a CSV

    More info: 
        https://docs.python.org/2/library/csv.html
    """
    writer = csv.writer(response)

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
    # instantiate the HttpResponse
    response = create_csv_response()

    # instantiate the csv.writer object
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


def export_selected_comments_csv(modeladmin, request, queryset):
    """
    Admin action that dumps selected comments into a CSV file

    Args:
        modeladmin: the current ModelAdmin the action is used in
        request: the HttpRequest object
        queryset: the set of objects selected by the user

    Returns:
        an HttpResponse object containing the CSV file to be downloaded

    More info:
        https://docs.djangoproject.com/en/1.10/ref/contrib/admin/actions/
    """
    # instantiate the HttpResponse
    response = create_csv_response()

    # instantiate the csv.writer object
    writer = create_comments_csv_writer(response)

    for comment in queryset:
        writer.writerow([
            smart_str(comment.respondent),
            smart_str(comment.question),
            smart_str(comment.message),
            smart_str(comment.language),
            smart_str(comment.tag),
            smart_str(comment.timestamp)
        ])

    return response

export_selected_comments_csv.short_description = "Export selected comments as a CSV"


def create_commentratings_csv_writer(response):
    """
    Create a csv.writer object for dumping CommentRatings
    Helper function for export_all_commentratings_csv, export_selected_comments_csv

    Returns:
        a Writer object for dumping CommentRatings into a CSV

    More info:
        https://docs.python.org/2/library/csv.html
    """
    writer = csv.writer(response)

    # write the column headers in the table
    writer.writerow([
        smart_str(u"Respondent"),
        smart_str(u"Comment"),
        smart_str(u"Score"),
        smart_str(u"Timestamp")
    ])

    return writer


def export_all_commentratings_csv(modeladmin, request, queryset):
    """
    Admin action that dumps all CommentRatings into a CSV file

    Args:
        modeladmin: the current ModelAdmin the action is used in
        request: the HttpRequest object
        queryset: the set of objects selected by the user

    Returns:
        an HttpResponse object containing the CSV file to be downloaded

    More info:
        https://docs.djangoproject.com/en/1.10/ref/contrib/admin/actions/
    """
    # instantiate the HttpResponse
    response = create_csv_response()

    # instantiate the csv.writer object
    writer = create_commentratings_csv_writer(response)

    # write the rows in the table
    commentratings = CommentRating.objects.all()
    for rating in commentratings:
        writer.writerow([
            smart_str(rating.respondent),
            smart_str(rating.comment),
            smart_str(rating.score),
            smart_str(rating.timestamp)
        ])

    return response

export_all_commentratings_csv.short_description = "Export all ratings as a CSV (select one first)"


def export_selected_commentratings_csv(modeladmin, request, queryset):
    """
    Admin action that dumps selected comments into a CSV file

    Args:
        modeladmin: the current ModelAdmin the action is used in
        request: the HttpRequest object
        queryset: the set of objects selected by the user

    Returns:
        an HttpResponse object containing the CSV file to be downloaded

    More info:
        https://docs.djangoproject.com/en/1.10/ref/contrib/admin/actions/
    """
    # instantiate the HttpResponse
    response = create_csv_response()

    # instantiate the csv.writer object
    writer = create_commentratings_csv_writer(response)

    # write the rows in the table
    for rating in queryset:
        writer.writerow([
            smart_str(rating.respondent),
            smart_str(rating.comment),
            smart_str(rating.score),
            smart_str(rating.timestamp)
        ])

    return response

export_selected_commentratings_csv.short_description = "Export selected ratings as a CSV"


def create_quantitativequestionrating_csv_writer(response):
    """
    Create a csv.writer object for dumping QuantitativeQuestionRatings
    Helper function for export_all_commentratings_csv, export_selected_quantitativequestionratings_csv

    Returns:
        a Writer object for dumping QuantitativeQuestionRatings into a CSV

    More info:
        https://docs.python.org/2/library/csv.html
    """
    writer = csv.writer(response)

    # write the column headers in the table
    writer.writerow([
        smart_str(u"Respondent"),
        smart_str(u"Question"),
        smart_str(u"Score"),
        smart_str(u"Timestamp")
    ])

    return writer

def export_all_quantitativequestionratings_csv(modeladmin, request, queryset):
    """
    Admin action that dumps all QuantitativeQuestionRatings into a CSV file

    Args:
        modeladmin: the current ModelAdmin the action is used in
        request: the HttpRequest object
        queryset: the set of objects selected by the user

    Returns:
        an HttpResponse object containing the CSV file to be downloaded

    More info:
        https://docs.djangoproject.com/en/1.10/ref/contrib/admin/actions/
    """
    # instantiate the HttpResponse
    response = create_csv_response()

    # instantiate the csv.writer object
    writer = create_quantitativequestionrating_csv_writer(response)

    # write the rows in the table
    commentratings = QuantitativeQuestionRating.objects.all()
    for rating in commentratings:
        writer.writerow([
            smart_str(rating.respondent),
            smart_str(rating.question),
            smart_str(rating.score),
            smart_str(rating.timestamp)
        ])

    return response

export_all_quantitativequestionratings_csv.short_description = "Export all quantitative question ratings as a CSV (select one first)"


def export_selected_quantitativequestionratings_csv(modeladmin, request, queryset):
    """
    Admin action that dumps selected QuantitativeQuestionRatings into a CSV file

    Args:
        modeladmin: the current ModelAdmin the action is used in
        request: the HttpRequest object
        queryset: the set of objects selected by the user

    Returns:
        an HttpResponse object containing the CSV file to be downloaded

    More info:
        https://docs.djangoproject.com/en/1.10/ref/contrib/admin/actions/
    """
    # instantiate the HttpResponse
    response = create_csv_response()

    # instantiate the csv.writer object
    writer = create_quantitativequestionrating_csv_writer(response)

    # write the rows in the table
    for rating in queryset:
        writer.writerow([
            smart_str(rating.respondent),
            smart_str(rating.question),
            smart_str(rating.score),
            smart_str(rating.timestamp)
        ])

    return response

export_selected_quantitativequestionratings_csv.short_description = "Export selected quantitative question ratings as a CSV"


