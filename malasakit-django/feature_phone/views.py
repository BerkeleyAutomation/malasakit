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
import numpy as np
from twilio.twiml.voice_response import VoiceResponse

from feature_phone.models import Respondent, Question, Response
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


def get_quantitative_questions():
    questions = Question.objects.filter(Q(related_object_id__isnull=True))
    return [question for question in questions if questions.related_object.active]


def play_recording(voice_response, recording):
    """
    Play a voice recording, either from a file or using speech synthesis.
    """
    if recording.recording:
        pass # voice_response.play_recording()
    # voice_response.say()


@csrf_exempt
@require_POST
def landing(request):
    """ The landing endpoint plays a welcome message and initializes the session. """
    if 'respondent-pk' not in request.session:
        related_object = web_models.Respondent.objects.create()
        respondent = Respondent.objects.create(related_object=related_object)
        request.session['respondent-pk'] = respondent.pk

    intro = VoiceResponse()
    intro.say('Welcome to Malasakit. We look forward to hearing from you on '
              'how your Barangay can better prepare for natural disasters.')
    # play_recording(intro, )
    intro.pause(1)
    intro.redirect(reverse('feature_phone:quantitative-questions'))
    return HttpResponse(intro)


@csrf_exempt
@require_POST
def quantitative_questions(request):
    response = VoiceResponse()
    response.say('In a few moments, we will ask you to rate a series of '
                 "statements. You may either use your phone's keypad "
                 'or speak your response.')
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
    print(request.POST)
    response = VoiceResponse()
    response.pause(1)
    response.say('Thank you for your time.')
    return HttpResponse(response)


@csrf_exempt
@require_POST
def error(request):
    response = VoiceResponse()
    response.say('Our apologies: Malasakit is temporarily not available. '
                 'Please try again momentarily.')
    return HttpResponse(response)
