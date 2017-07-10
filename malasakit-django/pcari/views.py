"""
This module defines the application's views, which are needed to render pages.
"""

# Standard library
from __future__ import unicode_literals
import datetime
import logging
import json
import math
import mimetypes
import random
import time

# Third-party libraries
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST
from django.urls import reverse
from django.utils import translation
from django.utils.translation import ugettext_lazy as _, ugettext
import numpy as np
from openpyxl import Workbook
import unicodecsv as csv

# Local modules and models
from pcari.models import Respondent
from pcari.models import QuantitativeQuestion, QualitativeQuestion
from pcari.models import Comment, CommentRating, QuantitativeQuestionRating
from pcari.models import MODELS, get_concrete_fields

__all__ = [
    'generate_ratings_matrix',
    'normalize_ratings_matrix',
    'calculate_principal_components',
    'fetch_comments',
    'fetch_qualitative_questions',
    'fetch_quantitative_questions',
    'fetch_question_ratings',
    'save_response',
    'export_data',
    'index',
    'landing',
    'qualitative_questions',
    'peer_responses',
    'rate_comments',
    'qualitative_questions',
    'personal_information',
    'end',
    'handle_page_not_found',
    'handle_internal_server_error',
]

DEFAULT_LANGUAGE = settings.LANGUAGE_CODE
DEFAULT_COMMENT_LIMIT = 300   # Default maximum number of comments to send
DEFAULT_STANDARD_ERROR = 4.5  # For comments with fewer than two ratings

LOGGER = logging.getLogger('pcari')


def profile(function):
    """
    Add a hook to a function to log runtime.

    Args:
        function: The callable to profile.

    Returns:
        A wrapped version of `function` with the same behavior.
    """
    def wrapper(*args, **kwargs):
        """ Return the result of the given `function`. """
        start_time = time.time()
        result = function(*args, **kwargs)
        end_time = time.time()
        time_elapsed = end_time - start_time
        LOGGER.log(logging.DEBUG, 'Call to "%s" took %.3f seconds',
                   function.__name__, time_elapsed)
        return result
    return wrapper


@profile
def generate_ratings_matrix():
    """
    Fetch quantitative question ratings in the form of a NumPy matrix.

    Each row in the matrix is the ratings of one respondent, and each column is
    the ratings for one question.

    Returns:
        respondent_id_map: A length-`m` dictionary mapping respondent identifiers
            to matrix row indicies.
        question_id_map: A length-`n` dictionary mapping quantitative question
            identifiers to matrix column indicies.
        ratings_matrix: A `m` x `n` NumPy array of ratings.

    Only active respondents, active questions, and active ratings are used.
    """
    respondent_ids = Respondent.objects.filter(active=True).values_list('id', flat=True)
    question_ids = QuantitativeQuestion.objects.filter(active=True).values_list('id', flat=True)

    respondent_id_map = {key: index for index, key in enumerate(respondent_ids)}
    question_id_map = {key: index for index, key in enumerate(question_ids)}

    shape = len(respondent_id_map), len(question_id_map)
    ratings_matrix = np.full(shape, np.nan)

    values = QuantitativeQuestionRating.objects.filter(respondent__active=True,
                                                       question__active=True,
                                                       active=True)
    excluded = [QuantitativeQuestionRating.SKIPPED,
                QuantitativeQuestionRating.NOT_RATED]
    features = 'respondent_id', 'question_id', 'score'
    values = values.exclude(score__in=excluded).values_list(*features)

    for respondent_id, question_id, score in values:
        row_index = respondent_id_map[respondent_id]
        column_index = question_id_map[question_id]
        ratings_matrix[row_index, column_index] = score

    return respondent_id_map, question_id_map, ratings_matrix


@profile
def normalize_ratings_matrix(ratings_matrix):
    """
    Normalize a ratings matrix so the ellipsoid of ratings is centered at the
    origin, and missing values are imputed with zero. (That is, the mean of the
    column before centering.)

    Args:
        ratings_matrix: A `m` x `n` matrix of ratings.

    Returns:
        A `m` x `n` matrix of normalized ratings with no `np.nan` values.
    """
    means_of_columns = np.nanmean(ratings_matrix, axis=0)
    return np.nan_to_num(ratings_matrix - means_of_columns)


@profile
def calculate_principal_components(normalized_ratings, num_components=2):
    """
    Calculate the principal components of a normalized ratings matrix.

    Args:
        normalized_ratings: A normalized ratings matrix (as provided by
            `normalize_ratings_matrix`).
        num_components: The number of principal components to select (`p`).

    Returns:
        A `p` x `n` NumPy array whose rows are principal components (`n` is the
        number of features).
    """
    _, _, covariance_matrix = np.linalg.svd(normalized_ratings, full_matrices=False)
    return covariance_matrix[:num_components]


@profile
@require_GET
def fetch_comments(request):
    """
    Fetch a list of comments as JSON.

    Args:
        request: May contain a `limit` GET parameter that specifies how many
            comments to get (by default: 1000).

    Returns:
        A `JsonResponse` containing an JSON object mapping comment identifiers
        to JSON objects with the following attributes:
            msg: The comment's message (from the `Comment.message` field).
            sem: The standard error of the mean.
            pos: The position of the comment. Obtained by projecting the
                 quantitative question ratings vector of the comment author
                 onto the first two principal components of the question
                 ratings dataset. This is a list containing two numbers, the
                 first principal component projection and second, respectively.
            tag: A short description of the comment's message.
            qid: The identifier of the `QualitativeQuestion` this comment was
                 in response to.
    """
    try:
        limit = int(request.GET.get('limit', str(DEFAULT_COMMENT_LIMIT)))
    except ValueError as error:
        return HttpResponseBadRequest(str(error))

    query = Comment.objects.filter(active=True, flagged=False)
    comments = query.exclude(message='').all()
    if len(comments) > limit:
        comments = random.sample(comments, limit)

    respondent_id_map, _, ratings = generate_ratings_matrix()
    if ratings.size:
        normalized_ratings = normalize_ratings_matrix(ratings)
        components = calculate_principal_components(normalized_ratings, 2)

    data = {}
    for comment in comments:
        standard_error = comment.score_sem
        row_index = respondent_id_map[comment.respondent.id]
        position = [0, 0]
        if ratings.size:
            position = list(np.round(components.dot(normalized_ratings[row_index, :]), 3))

        # Projects the ratings by this comment's author onto the first two
        # principal components to generate the position (`pos`).
        if math.isnan(standard_error):
            standard_error = DEFAULT_STANDARD_ERROR
        data[str(comment.id)] = {
            'msg': comment.message,
            'sem': round(standard_error, 3),
            'pos': position,
            'tag': comment.tag,
            'qid': comment.question_id
        }

    return JsonResponse(data)


def translate(text, language_code):
    translation.activate(language_code)
    return ugettext(text)


@profile
@require_GET
def fetch_qualitative_questions(request):
    """ Fetch qualitative question data as JSON. """
    # pylint: disable=unused-argument
    return JsonResponse({
        str(question.id): {
            code: translate(question.prompt, code)
            for code, _ in settings.LANGUAGES
        } for question in QualitativeQuestion.objects.filter(active=True)
    })


@profile
@require_GET
def fetch_quantitative_questions(request):
    """ Fetch quantitative question data as JSON. """
    # pylint: disable=unused-argument
    return JsonResponse({
        str(question.id): {
            'prompts': {
                code: translate(question.prompt, code)
                for code, _ in settings.LANGUAGES
            },
            'left-anchors': {
                code: translate(question.left_anchor, code)
                for code, _ in settings.LANGUAGES
            },
            'right-anchors': {
                code: translate(question.right_anchor, code)
                for code, _ in settings.LANGUAGES
            },
            'min-score': question.min_score,
            'max-score': question.max_score,
            'input-type': question.input_type,
        } for question in QuantitativeQuestion.objects.filter(active=True)
    })


@profile
@require_GET
def fetch_question_ratings(request):
    """
    Fetch quantitative question ratings as JSON.

    Args:
        request: The request is ignored.

    Returns:
        A `JsonResponse` containing a JSON object mapping quantitative question
        rating identifiers to rating objects, each with two keys:
            qid: The quantitative question identifier.
            score: How this question was rated.
    """
    # pylint: disable=unused-argument
    ratings = QuantitativeQuestionRating.objects
    ratings = ratings.filter(active=True, question__active=True)
    return JsonResponse({
        str(rating.id): {
            'qid': rating.question_id,
            'score': rating.score,
        } for rating in ratings
    })


@profile
def make_question_ratings(respondent, responses):
    """ Generate new quantitative question model instances. """
    for question_id, score in responses.get('question-ratings', {}).iteritems():
        yield QuantitativeQuestionRating(respondent=respondent,
                                         question_id=int(question_id), score=score)


@profile
def make_comments(respondent, responses):
    """ Generate new comment model instances. """
    for question_id, message in responses.get('comments', {}).iteritems():
        yield Comment(respondent=respondent, question_id=int(question_id),
                      language=respondent.language, message=message.strip())


@profile
def make_comment_ratings(respondent, responses):
    """ Generate new comment rating instances. """
    for comment_id, score in responses.get('comment-ratings', {}).iteritems():
        yield CommentRating(respondent=respondent, comment_id=int(comment_id),
                            score=score)


@profile
def make_respondent_data(respondent, responses):
    """ Save respondent data from a given response object. """
    respondent_data = responses.get('respondent-data', {})
    attributes = ['age', 'gender', 'location', 'submitted_personal_data',
                  'completed_survey']
    for attribute in attributes:
        serialized_name = attribute.replace('_', '-')
        if serialized_name in respondent_data:
            setattr(respondent, attribute, respondent_data[serialized_name])
    respondent.language = respondent_data['language']
    yield respondent


@profile
@require_POST
def save_response(request):
    """
    Write a single user's responses as a JSON object to the database.

    The request body should contain the string representation of a JSON object
    (that is, a Python dictionary) of the following form:

        {
            "question-ratings": {
                <qid>: <score>,
                ...
            },
            "comments": [
                <qid>: <message>,
                ...
            ],
            "comment-ratings": [
                <cid>: <score>,
                ...
            ],
            "respondent-data": {
                "age": ...,
                "gender": ...,
                "location": ...,
                "language": ...,
                "submitted-personal-data": ...,
                "completed-survey": ...
            }
        }

    In cases where the data were successfully received but the contents of the
    request are syntactically or logically incorrect (for instance, providing
    the `id` of a question that does not exist, or malformed JSON), no models
    are written to the database, and a general HTTP error code of 400 is
    returned. The error code indicates that the client should not send another
    request without modifications to the request's body.
    """
    respondent = Respondent()
    respondent.save()

    try:
        responses = json.loads(request.body)
        model_instances = []

        model_generator_functions = [
            make_respondent_data,
            make_question_ratings,
            make_comments,
            make_comment_ratings,
        ]

        for model_generator in model_generator_functions:
            model_instances.extend(model_generator(respondent, responses))

        for instance in model_instances:
            instance.full_clean()
    except (KeyError, ValueError, AttributeError, ObjectDoesNotExist,
            ValidationError) as error:
        respondent.delete()
        LOGGER.log(logging.ERROR, error)
        return HttpResponseBadRequest(str(error))

    for instance in model_instances:
        instance.save()
        LOGGER.log(logging.DEBUG, 'Saved instance %s', instance)
    return HttpResponse()


@profile
def export_csv(stream, queryset):
    """
    Export the given `QuerySet` as comma-separated values to a stream.

    Args:
        stream: A `file`-like object with a `write` method.
        queryset: A Django `QuerySet` of instances to export.

    Returns:
        None. Has a side effect of writing to the `stream`.
    """
    concrete_fields = get_concrete_fields(queryset.model)
    field_names = [unicode(field.get_attname()) for field in concrete_fields]

    writer = csv.writer(stream, encoding='utf-8')
    writer.writerow(field_names)

    for instance in queryset.iterator():
        row = [getattr(instance, field_name) for field_name in field_names]
        row = [unicode(cell) if cell is not None else '' for cell in row]
        writer.writerow(row)


@profile
def export_excel(stream, queryset):
    """
    Export the given `QuerySet` as an Excel spreadsheet.

    Args:
        stream: A `file`-like object with a `write` method.
        queryset: A Django `QuerySet` of instances to export.

    Returns:
        None. Has a side effect of writing to the `stream`.
    """
    concrete_fields = get_concrete_fields(queryset.model)
    field_names = [unicode(field.get_attname()) for field in concrete_fields]

    workbook = Workbook(write_only=True)
    worksheet = workbook.create_sheet(queryset.model.__name__)
    worksheet.append(field_names)

    for instance in queryset.iterator():
        row = [getattr(instance, field_name) for field_name in field_names]
        worksheet.append(row)

    workbook.save(stream)


def generate_export_filename(model_name, data_format):
    now = datetime.datetime.now()
    return model_name + '-' + now.strftime('%Y-%m-%d') + '.' + data_format


@profile
@staff_member_required
@require_GET
def export_data(request):
    """
    Export data for a model as a file.

    Args:
        request: A request object that supports the following GET parameters:
            model: The name of the model to export data for. This is a requred
                parameter.
            data_format: The name of the data format (default: csv). Supported
                options are: csv.
            keys: A comma-separated list of primary keys (default: select all
                instances). Only works for numeric primary keys.

    Returns:
        An `HttpResponse` that contains a file.
    """
    data_format = request.GET.get('format', 'csv')
    export_functions = {
        'csv': export_csv,
        'xlsx': export_excel,
    }
    try:
        export = export_functions[data_format]
    except KeyError:
        return HttpResponseBadRequest('no such data format')

    try:
        model_name = request.GET['model']
        model = MODELS[model_name]
    except KeyError:
        return HttpResponseBadRequest('no such model')

    queryset = model.objects
    primary_keys = request.GET.get('keys', None)
    if primary_keys is not None:
        primary_keys = list(map(int, primary_keys.split(',')))
        queryset = queryset.filter(pk__in=primary_keys)

    filename = generate_export_filename(model_name, data_format)
    content_type, _ = mimetypes.guess_type(filename)
    response = HttpResponse(content_type=content_type)
    response['Content-Disposition'] = 'attachment; filename="{0}"'.format(filename)
    export(response, queryset)
    return response


@profile
def index(request):
    """ Redirect the user to the `landing` page. """
    # pylint: disable=unused-argument
    return redirect(reverse('pcari:landing'))


@profile
@ensure_csrf_cookie
def landing(request):
    """ Render a landing page. """
    context = {'num_responses': Respondent.objects.filter(active=True).count()}
    return render(request, 'landing.html', context)


@profile
@ensure_csrf_cookie
def quantitative_questions(request):
    """ Render a page asking respondents to rate statements. """
    return render(request, 'quantitative-questions.html')


@profile
@ensure_csrf_cookie
def peer_responses(request):
    """ Render a page showing respondents how others rated the quantitative questions. """
    context = {'questions': QuantitativeQuestion.objects.filter(active=True).all()}
    return render(request, 'peer-responses.html', context)


@profile
@ensure_csrf_cookie
def rate_comments(request):
    """ Render a bloom page where respondents can rate comments by others. """
    return render(request, 'rate-comments.html')


@profile
@ensure_csrf_cookie
def qualitative_questions(request):
    """ Render a page asking respondents for comments (i.e. suggestions). """
    context = {'questions': QualitativeQuestion.objects.filter(active=True).all()}
    return render(request, 'qualitative-questions.html', context)


@profile
@ensure_csrf_cookie
def personal_information(request):
    """ Render a page asking respondents for personal information. """
    return render(request, 'personal-information.html')


@profile
@ensure_csrf_cookie
def end(request):
    """ Render an end-of-survey page. """
    return render(request, 'end.html')


@profile
def handle_page_not_found(request):
    """ Render a page for HTTP 404 errors (page not found). """
    context = {'heading': _('Page Not Found'),
               'message': _('The requested page does not appear to exist.')}
    return render(request, 'error.html', context)


@profile
def handle_internal_server_error(request):
    """ Render a page for HTTP 500 errors (internal server error). """
    context = {'heading': _('Internal Error'),
               'message': _('The server is currently experiencing some issues. '
                            'Please let the maintainers know immediately.')}
    return render(request, 'error.html', context)
