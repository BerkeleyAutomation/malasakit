"""
This module defines the application's views, which are needed to render pages.

"Pages" are generated in TwiML (Twilio Markup Language) for Twilio to play
desired audio.

See https://www.twilio.com/docs/api/twiml and
https://twilio.github.io/twilio-python/6.5.0/twiml/
"""

import random
import requests
from tempfile import TemporaryFile

from django.core.files import File
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.utils.translation import get_language
import numpy as np
from twilio.twiml.voice_response import VoiceResponse

from feature_phone.models import Respondent, Question, Response, Instructions
from pcari import models as web_models
from pcari.views import DEFAULT_COMMENT_LIMIT
from pcari.models import QuantitativeQuestion, QualitativeQuestion
from pcari.models import Comment, CommentRating, QuantitativeQuestionRating
from pcari.models import get_concrete_fields


def select_comments():
    comment_content_type = ContentType.objects.get(app_label='pcari', model='comment')
    voice_responses = Response.objects.filter(related_object_type=comment_content_type)
    comment_ids = list(voice_responses.values_list('related_object_id', flat=True))
    comment_ids = random.sample(comment_ids, min(len(comment_ids), DEFAULT_COMMENT_LIMIT))
    comments = list(Comment.objects.filter(id__in=comment_ids))
    if comments:
        standard_errors = np.array([comment.score_sem for comment in comments])
        probabilities = standard_errors/np.sum(standard_errors)
        return np.random.choice(comments, size=8, replace=False, p=probabilities)


def fetch_questions(question_type):
    questions = Question.objects.filter(related_object_type=question_type,
                                        language=get_language() or settings.LANGUAGE_CODE)
    # Need to use a list because the filter needs to access a field of `related_object`
    questions = [question for question in questions if question.related_object is None or
                                                       question.related_object.active]
    questions.sort(key=lambda quesiton: quesiton.related_object.order
                   if question.related_object and question.related_object.order
                   else float('inf'))
    return questions


def play_recording(response, recording):
    """
    Play a voice recording, either from a file or using speech synthesis.
    """
    if recording.recording.name:
        url = os.path.join(settings.MEDIA_URL, recording.recording.name)
        response.play(url)
    elif hasattr(recording, 'text'):
        response.say(recording.text)


@csrf_exempt
@require_POST
def landing(request):
    """ The landing endpoint plays a welcome message and initializes the session. """
    if 'respondent-pk' not in request.session:
        related_object = web_models.Respondent.objects.create()
        respondent = Respondent.objects.create(related_object=related_object)
        request.session['respondent-pk'] = respondent.pk

    response = VoiceResponse()
    play_recording(response, Instructions.objects.get(key='welcome'))
    response.pause(1)
    response.redirect(reverse('feature_phone:quantitative-questions'))
    return HttpResponse(response)


@csrf_exempt
@require_POST
def quantitative_questions(request):
    question_type = ContentType.objects.get(app_label='pcari', model='quantitativequestion')
    request.session['quantitative-questions'] = fetch_questions(question_type)
    response = VoiceResponse()
    play_recording(response, Instructions.objects.get(key='quantitative-question-directions'))
    response.pause(1)
    response.redirect(reverse('feature_phone:ask-quantitative-question'))
    return HttpResponse(response)


@csrf_exempt
@require_POST
def ask_quantitative_question(request):
    response = VoiceResponse()
    response.say('How prepared are you for a typhoon?')
    response.pause(1)
    response.record(action=reverse('feature_phone:process-recording'),
                    finish_on_key='0123456789*#', max_length=30, play_beep=True)
    response.say('Sorry, we are not sure if you entered a response.')
    return HttpResponse(response)


@csrf_exempt
@require_POST
def process_recording(request):
    response = VoiceResponse()
    response.pause(1)
    response.say('Thank you for your time.')
    return HttpResponse(response)


@csrf_exempt
@require_POST
def error(request):
    response = VoiceResponse()
    response.say('Our apologies: Malasakit is experiencing issues at this time. '
                 'Please try again momentarily.')
    return HttpResponse(response)
