"""
This module defines the application's views, which are needed to render pages.

"Pages" are generated in TwiML (Twilio Markup Language) for Twilio to play
desired audio.

See https://www.twilio.com/docs/api/twiml and
https://twilio.github.io/twilio-python/6.5.0/twiml/
"""

import os
import random
import requests
import urllib

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

REPLAY_QUESTION_DIGIT = '*'
SKIP_QUESTION_DIGIT = '#'


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


def fetch_question_pks(question_type):
    questions = Question.objects.filter(related_object_type=question_type,
                                        language=get_language() or settings.LANGUAGE_CODE)
    # Need to use a list because the filter needs to access a field of `related_object`
    questions = [question for question in questions if question.related_object is None or
                                                       question.related_object.active]
    questions.sort(key=lambda question: question.related_object.order
                   if question.related_object and question.related_object.order
                   else float('inf'))
    return [question.pk for question in questions]


def play_recording(response, recording):
    """
    Play a voice recording, either from a file or using speech synthesis.
    """
    if recording.recording.name:
        url = os.path.join(settings.MEDIA_URL, recording.recording.name)
        response.play(url)
    elif recording.text:
        response.say(recording.text)


def save_recording(file_field, url):
    filename, _ = urllib.urlretrieve(url)
    with open(filename, 'wb+') as audio_file:
        file_field.save(os.path.basename(url), File(audio_file))


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
    request.session['quantitative-question-pks'] = fetch_question_pks(question_type)
    response = VoiceResponse()
    play_recording(response, Instructions.objects.get(key='quantitative-question-directions'))
    response.pause(1)
    response.redirect(reverse('feature_phone:ask-quantitative-question'))
    return HttpResponse(response)


@csrf_exempt
@require_POST
def ask_quantitative_question(request):
    response = VoiceResponse()
    if not request.session['quantitative-question-pks']:
        del request.session['quantitative-question-pks']
        response.say('Thank you for your time.')
        return HttpResponse(response)

    question = Question.objects.get(pk=request.session['quantitative-question-pks'][0])
    play_recording(response, question)
    response.record(action=reverse('feature_phone:process-quantitative-response'),
                    finish_on_key='0123456789*#', max_length=30, play_beep=True,
                    recording_status_callback=reverse('feature_phone:process-quantitative-recording'))
    return HttpResponse(response)


@csrf_exempt
@require_POST
def process_quantitative_response(request):
    response = VoiceResponse()
    response.redirect(reverse('feature_phone:ask-quantitative-question'))

    digit = request.POST.get('Digits', '')
    if digit == 'hangup':
        return HttpResponse()
    if digit == REPLAY_QUESTION_DIGIT:
        return HttpResponse(response)

    question_pk = request.session['quantitative-question-pks'].pop(0)
    question = Question.objects.get(pk=question_pk)
    request.session.modified = True

    respondent = Respondent.objects.get(pk=request.session['respondent-pk'])
    rating = web_models.QuantitativeQuestionRating.objects.create(
        question=question.related_object,
        respondent=respondent.related_object,
    )
    voice_response = Response.objects.create(
        respondent=respondent,
        prompt_type=ContentType.objects.get_for_model(Question),
        prompt_id=question_pk,
        text=digit,
        url=request.POST['RecordingUrl'],
        related_object_type=ContentType.objects.get_for_model(
            web_models.QuantitativeQuestion
        ),
        related_object=rating,
    )

    if voice_response.text.isdigit():
        rating.score = int(voice_response.text)
        rating.save()
    elif voice_response.text == SKIP_QUESTION_DIGIT:
        rating.score = rating.SKIPPED
        rating.save()
    return HttpResponse(response)


@csrf_exempt
@require_POST
def process_quantitative_recording(request):
    if 'RecordingUrl' in request.POST:
        try:
            url = request.POST['RecordingUrl']
            response = Response.objects.get(url=url)
            save_recording(response.recording, url)
        except Response.DoesNotExist:
            pass
    return HttpResponse()


@csrf_exempt
@require_POST
def error(request):
    response = VoiceResponse()
    response.say('Our apologies: Malasakit is experiencing issues at this time. '
                 'Please try again momentarily.')
    return HttpResponse(response)
