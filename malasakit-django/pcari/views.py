"""
This module defines the application's views, which are needed to render pages.

These views can be broadly categorized into two groups:
    * **API endpoints** that can dynamically send and receive data (typically
      as `JSON <http://www.json.org/>`_). The client can use these endpoints to
      operate asynchronously.
    * **HTML pages** that show up to users. These pages are typically largely
      static and lend themselves to caching by service workers.

References:
  * `Django Introduction to Views <https://docs.djangoproject.com/en/dev/topics/http/views/>`_
  * `View Decorators <https://docs.djangoproject.com/en/dev/topics/http/decorators/>`_
  * `Creating Files for Download <https://docs.djangoproject.com/en/dev/howto/outputting-csv/>`_
"""

from __future__ import unicode_literals
import datetime
import logging
import json
import mimetypes
import random
import time
from uuid import UUID

import decorator
from django.conf import settings
from django.db.models import OneToOneRel
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST
from django.views.generic.base import TemplateView
from django.utils import translation
from django.utils.decorators import method_decorator
from django.utils.html import escape as escape_html
from django.utils.translation import ugettext_lazy as _, ugettext
import numpy as np
from openpyxl import Workbook
import unicodecsv as csv

from pcari.models import Respondent, Location
from pcari.models import QuantitativeQuestion, OptionQuestion, QualitativeQuestion
from pcari.models import Comment, CommentRating, QuantitativeQuestionRating, OptionQuestionChoice
from pcari.models import get_concrete_fields

__all__ = [
    'generate_ratings_matrix',
    'normalize_ratings_matrix',
    'calculate_principal_components',
    'fetch_comments',
    'fetch_quantitative_questions',
    'fetch_option_questions',
    'fetch_qualitative_questions',
    'fetch_question_ratings',
    'save_response',
    'export_data',
    'landing',
    'qualitative_questions',
    'peer_responses',
    'handle_page_not_found',
    'handle_internal_server_error',
]

LOGGER = logging.getLogger('pcari')


@decorator.decorator
def profile(function, *args, **kwargs):
    """
    Log the runtime of a function call.

    Args:
        function: The callable to profile.
        args: Additional positional arguments to ``function``.
        kwargs: Additional keyword arguments to ``function``.

    Returns:
        The result of applying ``function`` to ``args`` and ``kwargs``.
    """
    start_time = time.time()
    result = function(*args, **kwargs)
    end_time = time.time()
    time_elapsed = end_time - start_time
    LOGGER.log(logging.DEBUG, 'Call to "%s" took %.3f seconds',
               function.__name__, time_elapsed)
    return result


@profile
def generate_ratings_matrix():
    """
    Fetch quantitative question ratings in the form of a :mod:`numpy` matrix.

    Each row in the matrix represents the ratings of one respondent, and each
    column represents the ratings for one question.

    Returns:
        tuple: Tuple of three items:
            * ``respondent_id_map`` (`dict`): A length-`m` map from respondent
              identifiers to matrix row indicies.
            * ``question_id_map`` (`dict`): A length-`n` map from quantitative
              question identifiers to matrix column indicies.
            * ``ratings_matrix`` (`numpy.ndarray`): An `m` by `n` NumPy array
              of ratings.

        Only active respondents, active questions, and active ratings are used
        (see :attr:`pcari.models.History.active`).
    """
    respondent_ids = Respondent.objects.values_list('id', flat=True)
    question_ids = QuantitativeQuestion.objects.values_list('id', flat=True)

    respondent_id_map = {key: index for index, key in enumerate(respondent_ids)}
    question_id_map = {key: index for index, key in enumerate(question_ids)}

    shape = len(respondent_id_map), len(question_id_map)
    ratings_matrix = np.full(shape, np.nan)

    values = QuantitativeQuestionRating.objects.filter(question__enabled=True)
    features = 'respondent_id', 'question_id', 'score'
    values = values.exclude(score=QuantitativeQuestionRating.SKIPPED).values_list(*features)

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
        ratings_matrix (numpy.ndarray): An `m` by `n` matrix of ratings (as
            provided by :func:`generate_ratings_matrix`).

    Returns:
        numpy.ndarray: An `m` by `n` matrix of normalized ratings with no
        ``np.nan`` values.
    """
    means_of_columns = np.nanmean(ratings_matrix, axis=0)
    return np.nan_to_num(ratings_matrix - means_of_columns)


@profile
def calculate_principal_components(normalized_ratings, num_components=2):
    """
    Calculate the principal components of a normalized ratings matrix.

    Args:
        normalized_ratings (numpy.ndarray): An `m` by `n` normalized ratings
            matrix (as provided by :func:`normalize_ratings_matrix`).
        num_components (int): The number of principal components to select
            (`p`).

    Returns:
        numpy.ndarray: A `p` by `n` matrix whose rows are principal components.
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
            comments to get (by default: 300). Very high limits may decrease
            performance noticeably.

    Returns:
        A ``JsonResponse`` containing an JSON object of the form::

            {
                "<comment.id>": {
                    "msg": "<comment.message>",
                    "sem": <comment.score_sem>,
                    "pos": <author question ratings projection>,
                    "tag": "<comment.tag>",
                    "qid": <comment.question_id>
                },
                ...
            }

        The ``pos`` property is calculated by projecting the quantitative
        question ratings vector of the comment's author onto the first two
        principal components of the question ratings dataset (from
        :func:`calculate_principal_components`). This property is a list
        containing two numbers: the first and second projections, respectively.
    """
    try:
        limit = int(request.GET.get('limit', unicode(settings.DEFAULT_COMMENT_LIMIT)))
    except ValueError as error:
        return HttpResponseBadRequest(unicode(error))

    comments = (Comment.objects.filter(original=None, question__enabled=True, flagged=False)
                .exclude(message='').all())
    if len(comments) > limit:
        comments = random.sample(comments, limit)

    respondent_id_map, _, ratings = generate_ratings_matrix()
    data_in_every_column = all(np.count_nonzero(~np.isnan(ratings[:, i]))
                               for i in range(ratings.shape[1])) and ratings.size
    if data_in_every_column:
        normalized_ratings = normalize_ratings_matrix(ratings)
        components = calculate_principal_components(normalized_ratings, 2)

    data = {}
    for comment in comments:
        standard_error = comment.score_sem
        row_index = respondent_id_map[comment.respondent.id]
        position = [0, 0]
        if data_in_every_column:
            position = list(np.round(components.dot(normalized_ratings[row_index, :]), 3))

        # Projects the ratings by this comment's author onto the first two
        # principal components to generate the position (`pos`).
        if standard_error is None:
            standard_error = settings.DEFAULT_STANDARD_ERROR
        data[unicode(comment.id)] = {
            'msg': escape_html(comment.message),
            'sem': round(standard_error, 3),
            'pos': position,
            'tag': escape_html(comment.tag),
            'qid': comment.question_id
        }

    return JsonResponse(data)


def translate(text, language_code):
    with translation.override(language_code):
        return ugettext(text)


@profile
@require_GET
def fetch_qualitative_questions(request):
    """
    Fetch qualitative question data as JSON.

    Args:
        request: This parameter is ignored.

    Returns:
        A ``JsonResponse`` containing a JSON object of the form::

            {
                "<question.id>": {
                    "<language-code>": "<translated question.prompt>",
                    ...
                },
                ...
            }

        Each language code is obtained from ``settings.LANGUAGES``.
    """
    # pylint: disable=unused-argument
    return JsonResponse({
        unicode(question.id): {
            code: escape_html(translate(question.prompt, code))
            for code, _ in settings.LANGUAGES
        } for question in QualitativeQuestion.objects.iterator()
    })


@profile
@require_GET
def fetch_quantitative_questions(request):
    """
    Fetch quantitative question data as JSON.

    Args:
        request: This parameter is ignored.

    Returns:
        A ``JsonResponse`` containing a JSON object of the form::

            [
                {
                    "id": <question.id>,
                    "prompts": {
                        "<language-code>": "<translated question.prompt>",
                        ...
                    },
                    "left-anchors": {
                        "<language-code>": "<translated question.left_anchor>",
                        ...
                    },
                    "right-anchors": {
                        "<language-code>": "<translated question.right_anchor>",
                        ...
                    },
                    "min-score": <question.min_score>,
                    "max-score": <question.max_score>,
                    "input-type": <question.input_type>,
                    "order": <question.order>,
                    "show-statistics": <question.show-statistics>
                },
                ...
            ]

        Each language code is obtained from ``settings.LANGUAGES``.
    """
    # pylint: disable=unused-argument
    return JsonResponse([
        {
            'id': question.id,
            'prompts': {
                code: escape_html(translate(question.prompt, code))
                for code, _ in settings.LANGUAGES
            },
            'left-anchors': {
                code: escape_html(translate(question.left_anchor, code))
                for code, _ in settings.LANGUAGES
            },
            'right-anchors': {
                code: escape_html(translate(question.right_anchor, code))
                for code, _ in settings.LANGUAGES
            },
            'min-score': question.min_score,
            'max-score': question.max_score,
            'input-type': question.input_type,
            'order': question.order,
            'enabled': question.enabled,
        } for question in QuantitativeQuestion.objects.iterator()
    ], safe=False)


@profile
@require_GET
def fetch_option_questions(request):
    """
    Fetch option question data as JSON.

    Args:
        request: This parameter is ignored.

    Returns:
        A ``JsonResponse`` containing a JSON object with the following structure::

          {
              "id": <question.id>,
              "prompts": {
                  "<language-code>": "<translated question.prompt>",
                  ...
              },
              "options": {
                  "<language-code>": ["<translated member of question.options>", ...],
                  ...
              },
              "input-type": "<question.input_type>",
              "order": <question.order>
          }
    """
    # pylint: disable=unused-argument
    return JsonResponse([
        {
            'id': question.id,
            'prompts': {
                code: escape_html(translate(question.prompt, code))
                for code, _ in settings.LANGUAGES
            },
            'options': {
                code: [escape_html(translate(option, code)) for option in question.options]
                for code, _ in settings.LANGUAGES
            },
            'input-type': question.input_type,
            'order': question.order,
        } for question in OptionQuestion.objects.iterator()
    ], safe=False)


@profile
@require_GET
def fetch_question_ratings(request):
    """
    Fetch quantitative question ratings as JSON.

    Args:
        request: This parameter is ignored.

    Returns:
        A ``JsonResponse`` containing a JSON object of the form::

            {
                "<rating.id>": {
                    "qid": <question.id>,
                    "score": <rating.score>
                },
                ...
            }
    """
    # pylint: disable=unused-argument
    ratings = QuantitativeQuestionRating.objects.filter(question__enabled=True)
    return JsonResponse({
        unicode(rating.id): {
            'qid': rating.question_id,
            'score': rating.score,
        } for rating in ratings
    })


@profile
@require_GET
def fetch_locations(request):
    """ Fetch locations as JSON. """
    locations = Location.objects
    if request.GET.get('enabled-only', True):
        locations = locations.filter(enabled=True)
    fields = ['country', 'province', 'municipality', 'division']
    return JsonResponse({
        unicode(location.pk): {field: getattr(location, field) for field in fields}
        for location in locations.iterator()
    })


@profile
def make_question_ratings(respondent, response):
    """ Generate new quantitative question model instances. """
    # pylint: disable=no-member
    for question_id, score in response.get('question-ratings', {}).iteritems():
        QuantitativeQuestionRating.objects.update_or_create(
            question_id=int(question_id),
            respondent=respondent,
            defaults={'score': score},
        )


@profile
def make_question_choices(respondent, response):
    """ Generate new option question choice instances. """
    # pylint: disable=no-member
    for question_id, choice in response.get('question-choices', {}).iteritems():
        OptionQuestionChoice.objects.update_or_create(
            question_id=int(question_id),
            respondent=respondent,
            defaults={'option': choice},
        )


@profile
def make_comments(respondent, response):
    """ Generate new comment model instances. """
    for question_id, message in response.get('comments', {}).iteritems():
        Comment.objects.update_or_create(
            question_id=int(question_id),
            respondent=respondent,
            defaults={
                'message': (message or '').strip(),
                'language': respondent.language,
            },
        )


@profile
def make_comment_ratings(respondent, response):
    """ Generate new comment rating instances. """
    # pylint: disable=no-member
    for comment_id, score in response.get('comment-ratings', {}).iteritems():
        CommentRating.objects.update_or_create(
            comment_id=int(comment_id),
            respondent=respondent,
            defaults={'score': score},
        )


@profile
def make_respondent_data(respondent, response):
    """ Save respondent data from a given response object. """
    respondent_data = response.get('respondent-data', {})
    attributes = [
        'age',
        'gender',
        'language',
        'submitted_personal_data',
        'completed_survey',
        'sector',
    ]
    for attribute in attributes:
        serialized_name = attribute.replace('_', '-')
        if serialized_name in respondent_data:
            setattr(respondent, attribute, respondent_data[serialized_name])

    division = respondent_data.get('division')
    if division:
        if respondent_data['division'] == 'other':
            new_division = respondent_data.get('new_division')
            if new_division:
                respondent.location = Location.objects.create(division=new_division)
        else:
            respondent.location = Location.objects.get(pk=int(division))
    respondent.save()


@profile
@require_POST
def save_response(request):
    """
    Write a single user's responses as a JSON object to the database.

    The request body should contain the string representation of a JSON object
    (that is, a Python `dict`) of the following form::

        {
            "question-ratings": {
                "<question.id>": <score>,
                ...
            },
            "question-choices": {
                "<question.id>": "<choice>",
                ...
            },
            "comments": [
                "<question.id>": "<message>",
                ...
            ],
            "comment-ratings": [
                "<comment.id>": <score>,
                ...
            ],
            "respondent-data": {
                "uuid": "<uuid>",
                "age": <age>,
                "gender": "<gender>",
                "location": "<location>",
                "language": "<language-code>",
                "submitted-personal-data": <bool>,
                "completed-survey": <bool>
            }
        }

    No validation is performed. Validation through ``full_clean`` should be
    performed during analysis.

    Returns:
        A ``HttpResponse`` with a status code of 200 if the data were saved
        successfully, or a ``HttpResponseBadRequest`` with a status code of 400
        otherwise. The general-purpose bad request response is returned when
        the data were successfully received, but contained syntactical or
        logical errors (for instance, providing the ``id`` of a nonexistent
        question, or malformed JSON). In that case, no new instances are
        written to the database, and the client should not send another request
        without modifications to the payload.
    """
    try:
        response = json.loads(request.body)
        uuid = response.get('respondent-data', {}).get('uuid', None)
        if uuid is None:
            respondent = Respondent.objects.create()
        else:
            respondent, _ = Respondent.objects.get_or_create(uuid=uuid)

        model_build_functions = [
            make_respondent_data,
            make_question_ratings,
            make_question_choices,
            make_comments,
            make_comment_ratings,
        ]

        for build_model_instances in model_build_functions:
            build_model_instances(respondent, response)
    except (ValueError, AttributeError) as error:
        message = type(error).__name__ + ': ' + unicode(error)
        LOGGER.log(logging.ERROR, message)
        respondent.delete()
        return HttpResponseBadRequest(message)

    return HttpResponse()


def select_fields_for_export(model):
    concrete_fields = get_concrete_fields(model)
    return [unicode(field.name) for field in concrete_fields if field
            if not isinstance(field, OneToOneRel)]


@profile
def export_csv(stream, queryset):
    """
    Export the given ``QuerySet`` as comma-separated values to a stream.

    Args:
        stream: A ``file``-like object with a ``write`` method.
        queryset: A Django ``QuerySet`` of instances to export.

    Returns:
        `None`. Has a side effect of writing to the ``stream``.
    """
    field_names = select_fields_for_export(queryset.model)

    writer = csv.writer(stream, encoding='utf-8')
    writer.writerow(field_names)

    for instance in queryset.iterator():
        row = [getattr(instance, field_name) for field_name in field_names]
        row = [unicode(cell) if cell is not None else '' for cell in row]
        writer.writerow(row)


@profile
def export_excel(stream, queryset):
    """
    Export the given ``QuerySet`` as an Excel spreadsheet.

    Args:
        stream: A ``file``-like object with a ``write`` method.
        queryset: A Django ``QuerySet`` of instances to export.

    Returns:
        `None`. Has a side effect of writing to the ``stream``.
    """
    field_names = select_fields_for_export(queryset.model)

    workbook = Workbook(write_only=True)
    worksheet = workbook.create_sheet(queryset.model.__name__)
    worksheet.append(field_names)

    for instance in queryset.iterator():
        row = [getattr(instance, field_name) for field_name in field_names]
        row.append([(unicode(value) if isinstance(value, UUID) else value)
                    for value in row])

    workbook.save(stream)


def generate_export_filename(model_name, data_format):
    now = datetime.datetime.now()
    return model_name + '-' + now.strftime('%Y-%m-%d') + '.' + data_format


@profile
def export_data(queryset, data_format='csv'):
    """
    Create and write data to a response as a file for download.

    Args:
        data_format (str): The file format the data should be exported as.
            Current options are: ``csv`` (default), ``xlsx``.
        queryset: The instances to export.

    Returns:
        An ``HttpResponse`` with the requested data as an attached file, or an
        ``HttpResponseBadRequest`` with a status code of 400 with an invalid
        ``data_format``.
    """
    export_functions = {
        'csv': export_csv,
        'xlsx': export_excel,
    }
    try:
        export = export_functions[data_format]
    except KeyError:
        return HttpResponseBadRequest('no such data format "{0}"'.format(data_format))

    model_name = queryset.model.__name__
    filename = generate_export_filename(model_name, data_format)
    content_type, _ = mimetypes.guess_type(filename)

    response = HttpResponse(content_type=content_type)
    response['Content-Disposition'] = 'attachment; filename="{0}"'.format(filename)
    export(response, queryset)
    return response


@method_decorator(profile, name='dispatch')
@method_decorator(ensure_csrf_cookie, name='dispatch')
class CSRFTemplateView(TemplateView):
    pass


@profile
@ensure_csrf_cookie
def landing(request):
    """ Render a landing page. """
    context = {'num_responses': Respondent.objects.count()}
    return render(request, 'landing.html', context)


@profile
@ensure_csrf_cookie
def peer_responses(request):
    """ Render a page showing respondents how others rated the quantitative questions. """
    questions = QuantitativeQuestion.objects.filter(enabled=True)
    questions = [question for question in questions if question.num_ratings]
    context = {'questions': questions}
    return render(request, 'peer-responses.html', context)


@profile
@ensure_csrf_cookie
def qualitative_questions(request):
    """ Render a page asking respondents for comments (i.e. suggestions). """
    context = {'questions': QualitativeQuestion.objects.all()}
    return render(request, 'qualitative-questions.html', context)


@profile
@ensure_csrf_cookie
def handle_page_not_found(request):
    """ Render a page for HTTP 404 errors (page not found). """
    context = {'heading': _('Page Not Found'),
               'message': _('The requested page does not appear to exist.')}
    return render(request, 'error.html', context)


@profile
@ensure_csrf_cookie
def handle_internal_server_error(request):
    """ Render a page for HTTP 500 errors (internal server error). """
    context = {'heading': _('Internal Error'),
               'message': _('The server is currently experiencing some issues. '
                            'Please let the maintainers know immediately.')}
    return render(request, 'error.html', context)
