"""
This module defines the application's views, which are needed to render pages.
"""

# Standard library
import logging
import json
import random
import time

# Third-party libraries
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
LOGGER = logging.getLogger('pcari')


def profile(function):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = function(*args, **kwargs)
        end = time.time()
        time_elapsed = end - start
        message = 'Call to {} took {:.3f} seconds'
        LOGGER.log(logging.INFO, message.format(function.__name__, time_elapsed))
        return result
    return wrapper


@profile
def generate_quantitative_question_ratings_matrix():
    """
    Fetches quantitative question ratings in the form of a numpy matrix.

    Each row corresponds to one respondent and each column corresponds to one
    question. Missing values are filled in with `np.nan`.

    Because we only pull ID numbers, this function runs in milliseconds.
    """
    respondent_ids = Respondent.objects.values_list('id', flat=True)
    question_ids = QuantitativeQuestion.objects.values_list('id', flat=True)
    respondents_id_map = {key: index for index, key in enumerate(respondent_ids)}
    questions_id_map = {key: index for index, key in enumerate(question_ids)}

    shape = (len(respondents_id_map), len(questions_id_map))
    ratings_matrix = np.full(shape, np.nan)

    features = 'respondent_id', 'question_id', 'score'
    values = QuantitativeQuestionRating.objects.values_list(*features)
    for respondent_id, question_id, score in values:
        row_index = respondents_id_map[respondent_id]
        column_index = questions_id_map[question_id]
        ratings_matrix[row_index, column_index] = score
    return question_ids, ratings_matrix


def return_principal_components(n=2):
    """
    Calculates and returns the first n principal components of the quantitative
    question ratings matrix.

    Args:
        n: number of principal components to return .

    Returns:
        A q x n Numpy matrix where q is number of questions. Each row is a
        principal component.
    """
    qids, ratings = generate_quantitative_question_ratings_matrix() # dim r x q
    # subtract means
    means = np.nanmean(ratings, axis=1)
    ratings = (ratings.T - means).T # broadcasting rules for numpy
    ratings = np.nan_to_num(ratings) # replace unanswered questions with mean

    U, s, VT = np.linalg.svd(ratings) # U is r x r, VT is q x q
    return VT[:n,:] # return first n rows


def select_comments(respondent, threshold=10):
    """
    TODO: finalize an algorithm for doing this (discuss) [PCA?]
    """
    data = generate_quantiative_question_ratings_matrix()
    question_ids_map, ratings_matrix = data
    mean_responses = data.nanmean(axis=0)
    data -= mean_responses  # Remove bias


def make_quantitative_question_ratings(respondent, responses):
    for rating_object in responses.get('quantitative-question-ratings', []):
        question = QuantitativeQuestion(id=rating_object['question-id'])
        yield QuantitativeQuestionRating(respondent=respondent,
                                         question=question,
                                         score=rating_object['score'])


def make_comments(respondent, responses):
    for comment_object in responses.get('comments', []):
        question = QualitativeQuestion(id=comment_object['question-id'])
        yield Comment(respondent=respondent, question=question,
                      language=respondent.language,
                      message=comment_object['message'])


def make_comment_ratings(respondent, responses):
    for rating_object in responses.get('comment-ratings', []):
        comment = Comment.objects.get(id=rating_object['comment-id'])
        yield CommentRating(respondent=respondent, comment=comment,
                            score=rating_object['score'])


def make_respondent_data(respondent, responses):
    respondent_data = responses.get('respondent-data', {})
    attributes = ['age', 'gender', 'location', 'language',
                  'submitted_personal_data', 'completed_survey']
    for attribute in attributes:
        serialized_name = attribute.replace('_', '-')
        if serialized_name in respondent_data:
            setattr(respondent, attribute, respondent_data[serialized_name])
    yield respondent


@require_POST
def save_response(request):
    """
    Write a single user's responses to the database.

    The request body should contain the string representation of a JSON object
    (that is, a Python dictionary) of the following form:

        {
            "quantitative-question-ratings": [
                {
                    "question-id": ...,
                    "score": ...
                },
                ...
            ],
            "comments": [
                {
                    "question-id": ...,
                    "message": ...
                },
                ...
            ],
            "comment-ratings": [
                {
                    "comment-id": ...,
                    "score": ...
                },
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
    request without modifications to the request's contents.
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


# @language_selectable
def landing(request):
    translation.activate('tl')
    request.session[translation.LANGUAGE_SESSION_KEY] = 'tl'
    context = {'num_responses': str(Respondent.objects.count())}
    return render(request, 'landing.html', context)


def quantitative_questions(request):
    questions = []
    i = 1
    for q in QuantitativeQuestion.objects.all():
        questions.append([i, str(i) + ". " + q.prompt, q.left_text, q.right_text])
        i += 1
    context = {'questions': questions}
    return render(request, 'quantitative_questions.html', context)


def rate_suggestions(request):
    ratings = [] # TODO (much the same as how quantitative_questions works)
    context = {'ratings': ratings}
    return render(request, 'rate_suggestions.html', context)


def end(request):
    return render(request, 'end.html')
