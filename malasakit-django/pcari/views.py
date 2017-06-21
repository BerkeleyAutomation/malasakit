"""
This module defines the application's views, which are needed to render pages.
"""
# pylint: disable=unused-import

# Standard library
import logging
import json
import math
import random
import time

# Third-party libraries
from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.views.decorators.http import require_GET, require_POST
from django.utils import translation
from django.urls import reverse
import numpy as np

# Local modules and models
from .models import Respondent
from .models import LANGUAGES
from .models import QuantitativeQuestion, QualitativeQuestion
from .models import Comment, CommentRating, QuantitativeQuestionRating

DEFAULT_LANGUAGE = settings.LANGUAGE_CODE
DEFAULT_COMMENT_LIMIT = 1000  # Default maximum number of comments to send
DEFAULT_STANDARD_ERROR = 4.5  # For comments with fewer than two ratings
STANDARD_ERROR_PRECISION = 6  # Number of decimal places

LOGGER = logging.getLogger('pcari')


def profile(function):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = function(*args, **kwargs)
        end_time = time.time()
        time_elapsed = end_time - start_time
        message = 'Call to {} took {:.3f} seconds'
        LOGGER.log(logging.INFO, message.format(function.__name__, time_elapsed))
        return result
    return wrapper


@profile
def generate_quantitative_question_ratings_matrix(respondents=None):
    """
    Fetches quantitative question ratings in the form of a numpy matrix.

    Each row corresponds to one respondent and each column corresponds to one
    question. Missing values are filled in with `np.nan`.

    Because we only pull the fields we need from the ORM, this function should
    run relatively quickly (on the order of milliseconds).

    Args:
        respondents: A `QuerySet` of respondents to select ratings from. If
                     `None` (which is the default value), select all
                     respondents.

    Returns:
        respondent_id_map: A length-`m` dictionary mapping respondent IDs to
                           row indices.
        question_id_map: A lenght-`n` dictionary mapping quantitative question
                         IDs to column indices.
        ratings_matrix: A `m` x `n` NumPy array of ratings.
    """
    if respondents is None:
        respondents = Respondent.objects.all()

    respondent_ids = respondents.values_list('id', flat=True)
    question_ids = QuantitativeQuestion.objects.values_list('id', flat=True)
    respondent_id_map = {key: index for index, key in enumerate(respondent_ids)}
    question_id_map = {key: index for index, key in enumerate(question_ids)}

    shape = (len(respondent_id_map), len(question_id_map))
    ratings_matrix = np.full(shape, np.nan)

    features = 'respondent_id', 'question_id', 'score_history_text'
    values = QuantitativeQuestionRating.objects.values_list(*features)
    for respondent_id, question_id, score_history_text in values:
        score = score_history_text.split(QuantitativeQuestionRating
                                         .SCORE_HISTORY_TEXT_DELIMIETER)[-1]
        row_index = respondent_id_map[respondent_id]
        column_index = question_id_map[question_id]
        ratings_matrix[row_index, column_index] = score

    return respondent_id_map, question_id_map, ratings_matrix


def normalize_ratings_matrix(ratings_matrix):
    """
    Normalize a ratings matrix.

    In this context, a normalized matrix is one where the mean row is the zero
    vector, and `np.nan` values are replaced by zero. (If the bias, or mean, is
    readded to every row, the missing values are replaced by its column's mean.)

    Args:
        ratings_matrix: A `m` x `n` matrix of ratings, where each row
                        represents a respondent.

    Returns:
        A `m` x `n` matrix of normalized ratings, which is guaranteed to have
        no `np.nan` values.
    """
    mean_ratings = np.nanmean(ratings_matrix, axis=0)
    normalized_ratings_matrix = np.nan_to_num(ratings_matrix - mean_ratings)
    return normalized_ratings_matrix


@profile
def calculate_principal_components(normalized_ratings, n=2):
    """
    Calculates the first `n` principal components of a normalized quantitative
    question ratings matrix.

    Args:
        n: number of principal components to calculate.

    Returns:
        A `n` x `q` Numpy matrix, where `q` is number of quantitative
        questions. Each row is a principal component.
    """
    U, S, VT = np.linalg.svd(normalized_ratings, full_matrices=False)
    return VT[:n, :]  # Slice the first `n` rows


@require_GET
def fetch_comments(request):
    """
    Fetch a list of comments as JSON.
    """
    try:
        limit = int(request.GET.get('limit', str(DEFAULT_COMMENT_LIMIT)))
    except ValueError as error:
        return HttpResponseBadRequest(str(error))

    comments = list(Comment.objects.all())
    if len(comments) > limit:
        comments = random.sample(comments, limit)

    ratings_data = generate_quantitative_question_ratings_matrix()
    respondent_id_map, question_id_map, ratings = ratings_data
    normalized_ratings = normalize_ratings_matrix(ratings)
    components = calculate_principal_components(normalized_ratings, 2)

    data = {}
    for comment in comments:
        if comment.message:
            standard_error = comment.standard_error
            row_index = respondent_id_map[comment.respondent.id]

            # Projects the ratings by this comment's author onto the first two
            # principal components
            ratings_by_respondent = normalized_ratings[row_index, :]
            position = list(np.round(components.dot(ratings_by_respondent), 6))

            if math.isnan(standard_error):
                standard_error = DEFAULT_STANDARD_ERROR
            data[str(comment.id)] = {
                'msg': comment.message,
                'sem': round(standard_error, STANDARD_ERROR_PRECISION),
                'pos': position,
                'tag': comment.tag,
                'qid': comment.question_id
            }

    return JsonResponse(data)


@require_GET
def fetch_qualitative_questions(request):
    return JsonResponse({str(question.id): question.prompt for question in
                         QualitativeQuestion.objects.all()})


def make_quantitative_question_ratings(respondent, responses):
    for question_id, scores in responses.get('question-ratings', {}).iteritems():
        question = QuantitativeQuestion(id=int(question_id))
        rating = QuantitativeQuestionRating(respondent=respondent,
                                            question=question)
        rating.score_history = scores
        yield rating


def make_comments(respondent, responses):
    for question_id, message in responses.get('comments', {}).iteritems():
        question = QualitativeQuestion(id=int(question_id))

        # Replaces empty messages with None so they can show up as placeholders in admin
        if message.strip() == "":
            message = None

        yield Comment(respondent=respondent, question=question,
                      language=respondent.language, message=message)


def make_comment_ratings(respondent, responses):
    for comment_id, scores in responses.get('comment-ratings', {}).iteritems():
        comment = Comment.objects.get(id=int(comment_id))
        rating = CommentRating(respondent=respondent, comment=comment)
        rating.score_history = scores
        yield rating


def make_respondent_data(respondent, responses):
    respondent_data = responses.get('respondent-data', {})
    attributes = ['age', 'gender', 'location', 'submitted_personal_data',
                  'completed_survey']
    for attribute in attributes:
        serialized_name = attribute.replace('_', '-')
        if serialized_name in respondent_data:
            setattr(respondent, attribute, respondent_data[serialized_name])
    respondent.language = respondent_data['language']
    yield respondent


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
            make_quantitative_question_ratings,
            make_comments,
            make_comment_ratings,
        ]

        for model_generator in model_generator_functions:
            model_instances.extend(model_generator(respondent, responses))
    except (KeyError, ValueError, ObjectDoesNotExist) as error:
        respondent.delete()
        LOGGER.log(logging.ERROR, error)
        return HttpResponseBadRequest(str(error))

    for instance in model_instances:
        instance.save()
    return HttpResponse()


def supported_languages():
    return [code for code, name in settings.LANGUAGES]


def language_selectable(view):
    def view_wrapper(request, *args, **kwargs):
        language_code = request.GET.get('lang')
        if language_code in supported_languages():
            translation.activate(language_code)
            request.session[translation.LANGUAGE_SESSION_KEY] = language_code
        return view(request, *args, **kwargs)
    return view_wrapper


def index(request):
    return redirect(reverse('pcari:landing'))


@language_selectable
def landing(request):
    context = {'num_responses': Respondent.objects.count()}
    return render(request, 'landing.html', context)


@language_selectable
def personal_information(request):
    config = apps.get_app_config('pcari')
    context = {'province_names': [(province_name['code'], province_name['name'])
                                  for province_name in config.province_names]}
    return render(request, 'personal-information.html', context)


@language_selectable
def quantitative_questions(request):
    context = {'questions': QuantitativeQuestion.objects.all()}
    return render(request, 'quantitative-questions.html', context)


@language_selectable
def response_histograms(request):
    return render(request, 'response-histograms.html')


@language_selectable
def rate_comments(request):
    ratings = [] # TODO (much the same as how quantitative_questions works)
    context = {'ratings': ratings}
    return render(request, 'rate-comments.html', context)


@language_selectable
def qualitative_questions(request):
    questions = QualitativeQuestion.objects.all()
    question_text = [(question.id, question.prompt) for question in questions]
    context = {'questions': question_text}
    return render(request, 'qualitative-questions.html', context)


@language_selectable
def end(request):
    return render(request, 'end.html')
