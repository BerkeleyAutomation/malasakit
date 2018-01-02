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
from urllib2 import urlopen

from django.core.files.base import ContentFile
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
from twilio.twiml.voice_response import VoiceResponse, Gather

from feature_phone.models import Respondent, Question, Response, Instructions
from pcari import models as web_models
from pcari.models import QuantitativeQuestion, QualitativeQuestion
from pcari.models import Comment, CommentRating, QuantitativeQuestionRating
from pcari.models import get_concrete_fields
from pcari.templatetags.localize_url import localize_url

REPLAY_QUESTION_DIGIT = '*'
SKIP_QUESTION_DIGIT = '#'
KEY_TO_LANGUAGE = {
    '0': 'en',
}


def select_comments(num_to_select=2):
    # TODO: add comment selection for those without backreferences, fix filter (strip whitespace)
    comments = web_models.Comment.objects.filter(
        language=get_language() or settings.LANGUAGE_CODE,
    ).exclude(message='')
    comment_data = comments.values('pk', 'message', 'score_sem')
    if not comment_data:
        return []

    standard_errors = [comment['score_sem'] for comment in comment_data]
    standard_errors = np.array([
        (error if error is not None else settings.DEFAULT_STANDARD_ERROR)
        for error in standard_errors
    ])
    probabilities = standard_errors/np.sum(standard_errors)
    return list(np.random.choice(comment_data, size=num_to_select, replace=False,
                                 p=probabilities))


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


def fetch_recording(file_field, url):
    response = urlopen(url)
    buffer = ContentFile(response.read())
    file_field.save(os.path.basename(url), buffer, save=True)


def make_response(respondent, prompt, related_object):
    return Response.objects.create(
        respondent=respondent,
        prompt_type=ContentType.objects.get_for_model(prompt.__class__),
        prompt_id=prompt.pk,
        related_object_type=ContentType.objects.get_for_model(related_object.__class__),
        related_object_id=related_object.pk,
    )


def transcribe_rating(voice_response, text=''):
    voice_response.text = text
    voice_response.save()

    rating = voice_response.related_object
    if rating:
        if voice_response.text.isdigit():
            rating.score = int(voice_response.text)
            rating.save()
        elif voice_response.text == SKIP_QUESTION_DIGIT:
            rating.score = rating.SKIPPED
            rating.save()


@csrf_exempt
@require_POST
def select_language(request):
    """ Prompts the user to select a language. """
    if 'respondent-pk' not in request.session:
        related_object = web_models.Respondent.objects.create()
        respondent = Respondent.objects.create(related_object=related_object)
        request.session['respondent-pk'] = respondent.pk

    response = VoiceResponse()
    gather = Gather(action=reverse('feature_phone:redirect-to-landing'),
                    finish_on_key='0123456789', num_digits=1,
                    timeout=settings.SPEECH_TIMEOUT)
    for prompt in Instructions.objects.filter(key='select-language'):
        play_recording(gather, prompt)
    response.append(gather)
    # TODO: add default response
    return HttpResponse(response)


@csrf_exempt
@require_POST
def redirect_to_landing(request):
    selected_language = KEY_TO_LANGUAGE.get(request.POST.get('Digits')) or settings.LANGUAGE_CODE
    respondent = Respondent.objects.get(pk=request.session['respondent-pk'])
    respondent.language = selected_language
    respondent.save()

    response = VoiceResponse()
    response.redirect(localize_url(reverse('feature_phone:landing'), selected_language))
    return HttpResponse(response)


@csrf_exempt
@require_POST
def landing(request):
    """ The landing endpoint plays a welcome message and initializes the session. """
    response = VoiceResponse()
    play_recording(response, Instructions.objects.get(key='welcome', language=get_language()))
    response.pause(0.5)
    response.redirect(reverse('feature_phone:quantitative-questions'))
    return HttpResponse(response)


@csrf_exempt
@require_POST
def quantitative_questions(request):
    question_type = ContentType.objects.get_for_model(web_models.QuantitativeQuestion)
    request.session['index'] = 0
    request.session['obj-keys'] = fetch_question_pks(question_type)

    response = VoiceResponse()
    play_recording(response, Instructions.objects.get(key='quantitative-question-directions',
                                                      language=get_language()))
    response.pause(0.5)
    play_recording(response, Instructions.objects.get(key='rating-controls',
                                                      language=get_language()))
    response.pause(1)
    response.redirect(reverse('feature_phone:ask-quantitative-question'))
    return HttpResponse(response)


@csrf_exempt
@require_POST
def ask_quantitative_question(request):
    response = VoiceResponse()
    index, question_pks = request.session['index'], request.session['obj-keys']
    if index >= len(question_pks):
        response.redirect(reverse('feature_phone:comments'))
        return HttpResponse(response)

    question = Question.objects.get(pk=question_pks[index])
    response.say('Question {} of {}.'.format(index + 1, len(question_pks)))
    play_recording(response, question)
    response.record(action=reverse('feature_phone:process-quantitative-response'),
                    finish_on_key='0123456789*#', max_length=30, play_beep=True,
                    recording_status_callback=reverse('feature_phone:download-recording'),
                    timeout=settings.SPEECH_TIMEOUT)
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

    index = request.session['index']
    question = Question.objects.get(pk=request.session['obj-keys'][index])

    respondent = Respondent.objects.get(pk=request.session['respondent-pk'])
    rating = web_models.QuantitativeQuestionRating.objects.create(
        question=question.related_object,
        respondent=respondent.related_object,
    )
    voice_response = make_response(respondent, question, rating)
    transcribe_rating(voice_response, digit)
    voice_response.url = request.POST['RecordingUrl']
    voice_response.save()
    request.session['index'] += 1
    return HttpResponse(response)


@csrf_exempt
@require_POST
def download_recording(request):
    if 'RecordingUrl' in request.POST:
        try:
            url = request.POST['RecordingUrl']
            voice_response = Response.objects.get(url=url)
            fetch_recording(voice_response.recording, url)
            voice_response.save()
        except Response.DoesNotExist:
            pass
    return HttpResponse()


@csrf_exempt
@require_POST
def comments(request):
    response = VoiceResponse()
    request.session['index'] = 0
    request.session['obj-keys'] = [comment['pk'] for comment in select_comments()]
    play_recording(response, Instructions.objects.get(key='rate-comments-directions',
                                                      language=get_language()))
    response.pause(1)
    response.redirect(reverse('feature_phone:play-comment'))
    return HttpResponse(response)


@csrf_exempt
@require_POST
def play_comment(request):
    response = VoiceResponse()
    index, comment_pks = request.session['index'], request.session['obj-keys']
    if index >= len(comment_pks):
        response.redirect(reverse('feature_phone:qualitative-questions'))
        return HttpResponse(response)

    response.say('Comment {} of {}.'.format(index + 1, len(comment_pks)))
    try:
        comment = Response.objects.get(related_object_id=comment_pks[index])
        play_recording(response, comment)
    except Response.DoesNotExist:
        comment = web_models.Comment.objects.get(pk=comment_pks[index])
        response.say(comment.message)
    response.record(action=reverse('feature_phone:process-comment-rating'),
                    finish_on_key='0123456789*#', max_length=30, play_beep=True,
                    recording_status_callback=reverse('feature_phone:download-recording'),
                    timeout=settings.SPEECH_TIMEOUT)
    return HttpResponse(response)


@csrf_exempt
@require_POST
def process_comment_rating(request):
    response = VoiceResponse()
    response.redirect(reverse('feature_phone:play-comment'))

    digit = request.POST.get('Digits', '')
    if digit == 'hangup':
        return HttpResponse()
    if digit == REPLAY_QUESTION_DIGIT:
        return HttpResponse(response)

    index = request.session['index']
    respondent = Respondent.objects.get(pk=request.session['respondent-pk'])
    comment = web_models.Comment.objects.get(pk=request.session['obj-keys'][index])
    comment, _ = Response.objects.get_or_create(related_object_id=comment.pk, defaults={
        'respondent': respondent,
        'prompt_type': ContentType.objects.get_for_model(Question),
        'related_object_type': ContentType.objects.get_for_model(web_models.Comment),
    })

    rating = web_models.CommentRating.objects.create(
        comment=comment.related_object,
        respondent=respondent.related_object,
    )
    voice_response = make_response(respondent, comment, rating)
    transcribe_rating(voice_response, digit)
    voice_response.url = request.POST['RecordingUrl']
    voice_response.save()

    request.session['index'] += 1
    return HttpResponse(response)


@csrf_exempt
@require_POST
def qualitative_questions(request):
    question_type = ContentType.objects.get_for_model(web_models.QualitativeQuestion)
    request.session['index'] = 0
    request.session['obj-keys'] = fetch_question_pks(question_type)

    response = VoiceResponse()
    play_recording(response, Instructions.objects.get(key='qualitative-question-directions',
                                                      language=get_language()))
    response.pause(0.5)
    response.redirect(reverse('feature_phone:ask-qualitative-question'))
    return HttpResponse(response)


@csrf_exempt
@require_POST
def ask_qualitative_question(request):
    response = VoiceResponse()
    index, question_pks = request.session['index'], request.session['obj-keys']
    if index >= len(question_pks):
        response.redirect(reverse('feature_phone:ask-age'))
        return HttpResponse(response)

    question = Question.objects.get(pk=question_pks[index])
    play_recording(response, question)
    response.record(action=reverse('feature_phone:process-comment'),
                    finish_on_key='0123456789*#', max_length=60, play_beep=True,
                    recording_status_callback=reverse('feature_phone:download-recording'),
                    timeout=settings.SPEECH_TIMEOUT)
    return HttpResponse(response)


@csrf_exempt
@require_POST
def process_comment(request):
    response = VoiceResponse()
    response.redirect(reverse('feature_phone:ask-qualitative-question'))

    digit = request.POST.get('Digits', '')
    if digit == 'hangup':
        return HttpResponse()
    if digit == REPLAY_QUESTION_DIGIT:
        return HttpResponse(response)

    index = request.session['index']
    question = Question.objects.get(pk=request.session['obj-keys'][index])

    respondent = Respondent.objects.get(pk=request.session['respondent-pk'])
    comment = web_models.Comment.objects.create(
        question=question.related_object,
        respondent=respondent.related_object,
        language=get_language() or '',
    )
    voice_response = make_response(respondent, question, comment)
    if digit != SKIP_QUESTION_DIGIT:
        voice_response.url = request.POST['RecordingUrl']
        voice_response.save()
    request.session['index'] += 1
    return HttpResponse(response)


@csrf_exempt
@require_POST
def ask_age(request):
    response = VoiceResponse()
    play_recording(response, Instructions.objects.get(key='personal-information-directions',
                                                      language=get_language()))
    response.pause(1)
    play_recording(response, Instructions.objects.get(key='age-prompt',
                                                      language=get_language()))
    response.record(action=reverse('feature_phone:process-age'),
                    finish_on_key=SKIP_QUESTION_DIGIT, max_length=30, play_beep=True,
                    recording_status_callback=reverse('feature_phone:record-age'),
                    timeout=settings.SPEECH_TIMEOUT)
    return HttpResponse(response)


@csrf_exempt
@require_POST
def process_age(request):
    respondent = Respondent.objects.get(pk=request.session['respondent-pk'])
    respondent.age_url = request.POST['RecordingUrl']
    respondent.save()

    response = VoiceResponse()
    response.redirect(reverse('feature_phone:ask-gender'))
    return HttpResponse(response)


@csrf_exempt
@require_POST
def ask_gender(request):
    response = VoiceResponse()
    response.pause(0.5)
    play_recording(response, Instructions.objects.get(key='gender-prompt',
                                                      language=get_language()))
    response.record(action=reverse('feature_phone:process-gender'),
                    finish_on_key=SKIP_QUESTION_DIGIT, max_length=30, play_beep=True,
                    recording_status_callback=reverse('feature_phone:record-gender'),
                    timeout=settings.SPEECH_TIMEOUT)
    return HttpResponse(response)


@csrf_exempt
@require_POST
def process_gender(request):
    respondent = Respondent.objects.get(pk=request.session['respondent-pk'])
    respondent.gender_url = request.POST['RecordingUrl']
    respondent.save()

    response = VoiceResponse()
    response.redirect(reverse('feature_phone:end'))
    return HttpResponse(response)


@csrf_exempt
@require_POST
def end(request):
    del request.session['respondent-pk']
    del request.session['index']
    del request.session['obj-keys']
    response = VoiceResponse()
    play_recording(response, Instructions.objects.get(key='thanks',
                                                      language=get_language()))
    response.hangup()
    return HttpResponse(response)


@csrf_exempt
@require_POST
def record_age(request):
    respondent = Respondent.objects.get(age_url=request.POST['RecordingUrl'])
    fetch_recording(respondent.age, request.POST['RecordingUrl'])
    return HttpResponse()


@csrf_exempt
@require_POST
def record_gender(request):
    respondent = Respondent.objects.get(gender_url=request.POST['RecordingUrl'])
    fetch_recording(respondent.gender, request.POST['RecordingUrl'])
    return HttpResponse()


@csrf_exempt
@require_POST
def error(request):
    response = VoiceResponse()
    response.say('Our apologies: Malasakit is experiencing issues at this time. '
                 'Please try again momentarily.')
    return HttpResponse(response)
