"""
This module defines the application's views, which are needed to render pages.

"Pages" are generated in TwiML (Twilio Markup Language) for Twilio to play
desired audio.

See https://www.twilio.com/docs/api/twiml and
https://twilio.github.io/twilio-python/6.5.0/twiml/
"""

import random
import requests

from django.core.files import File
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse

from twilio.twiml.voice_response import VoiceResponse

from feature_phone.models import Respondent, Question, Response

from pcari.models import QuantitativeQuestion, QualitativeQuestion
from pcari.models import Comment, CommentRating, QuantitativeQuestionRating
from pcari.models import get_concrete_fields

# Placeholder flow will yank content straight from v1.25 models

@csrf_exempt
def landing(request):
    """Landing page welcome message"""
    res = VoiceResponse()

    # REPLACE WITH INTRO INSTRUCTIONS
    res.say("Welcome to Malasakit.")
    res.say("You will be asked several questions about typhoon preparedness.")
    res.pause(1)
    # need a better way to flag down the first question in the sequence
    res.redirect(reverse('feature_phone:quantitative-questions', args=(1,)))

    # create a new Respondent and save to database
    user = Respondent()
    user.save()
    request.session['respondent_id'] = user.id # set current Respondent id in sessions

    print request.session['respondent_id']

    return HttpResponse(res)

@csrf_exempt
def personal_info(request):
    """Holding tight on this to see how we handle models and stuff"""
    pass

@csrf_exempt
def quantitative_questions(request):
    """Plays quantitative question."""
    res = VoiceResponse()

    user = Respondent.objects.get(id=request.session['respondent_id'])

    # query all questions for which user does NOT have a response
    # use related_object_type in RelatedObjectMixin

    # get all the quantitative question recordings
    questions = Question.objects.filter(related_object_type=ContentType.objects.get(
        app_label='pcari', model='quantitativequestion'))

    # get all the questions that user has not made responses for

    not_answered = [q for q in questions if q not in [r.prompt for r in Response.objects.filter(respondent=user)]]

    if len(not_answered) == 0:
        # we have answered all quantitative questions! redirect to comment rating phase
        res.redirect(reverse('feature_phone:rate-comments', args=(0,)))
    else:
        # redirect back after recording
        res.play(not_answered[0].recording.url) # play the first unanswered question

        # initialize response for user. this response will be filled in at process_recording
        user_response = Response()
        user_response.respondent = user

        # what quantitative question was this in response to?
        quant_q_model = not_answered[0].related_object

        user_response.related_object = QuantitativeQuestionRating(question=quant_q_model)

        user_response.save()

        # redirect back to quant question
        next_url = reverse('feature_phone:quantitative-questions')
        res.record(max_length=3, timeout=3,
                   action=reverse('feature_phone:process-recording', args=(next_url,)))

    return HttpResponse(res)

@csrf_exempt
def process_recording(request, next_url):
    """
    After saving the recording, redirect to the next url.
    Probably want to pass in a newly-created Recording model, and then
    fill in the FileField here.

    """
    user = Respondent.objects.get(id=request.session['respondent_id'])

    # User will have a Response without a recording field that was just created.
    user_responses = Response.objects.get(respondent=user)
    empty_response = None
    for r in user_responses:
        if not r.recording:
            empty_response = r

    # Recording might not be available yet, use recordingStatusCallback
    # while rendering Record verb.
    # https://www.twilio.com/docs/api/twiml/record#attributes-recording-status-callback

    recording_url = request.POST.get('RecordingUrl', 'NOT AVAILABLE')

    empty_response.recording = File(requests.get(recording_url).content,
                                    name="%s.mp3" % (empty_response.id))

    empty_response.save()

    res = VoiceResponse()

    # SAVE AUDIO RESPONSE HERE

    res.say("Recording saved.")

    res.redirect(next_url)
    return HttpResponse(res)

@csrf_exempt
def rate_comments(request, num_rated):
    """
    Can the user keep rating? Not sure. Let's assume no for now.
    """
    # cast again
    num_rated = int(num_rated)

    NUM_COMMENTS = 2 # maxinumber of comments to rate

    res = VoiceResponse()

    # REPLACE WITH SAMPLING CODE
    comments = Comment.objects.all()
    comment = comments[random.randint(1, len(comments))]

    res.say("This user made a suggestion. Please rate it from 0 to 9.")
    res.pause(1)
    res.say(comment.message)

    # Determine next url- another comment? or next phase
    if num_rated + 1 == NUM_COMMENTS:
        next_url = reverse('feature_phone:qualitative-questions', args=(1,))
    else:
        next_url = reverse('feature_phone:rate-comments', args=(num_rated + 1,))

    res.record(max_length=3, timeout=3,
               action=reverse('feature_phone:process-recording', args=(next_url,)))
    return HttpResponse(res)

@csrf_exempt
def qualitative_questions(request, question_id):
    """Plays qualitative question."""
    res = VoiceResponse()

    # cast to int
    question_id = int(question_id)

    try:
        # REPLACE WITH INSTRUCTIONS AND AUDIO FROM RECORDING
        question = QualitativeQuestion.objects.get(id=question_id)
        res.say("Now it's your turn to offer feedback. Please respond to this question. ")
        res.pause(1)
        res.say(question.prompt)

        # Determine next url- another question? or next phase
        if question_id + 1 in [q.id for q in QualitativeQuestion.objects.all()]:
            next_url = reverse('feature_phone:qualitative-questions', args=(question_id + 1,))
        else:
            next_url = reverse('feature_phone:end')

        res.record(max_length=20, timeout=20,
                   action=reverse('feature_phone:process-recording', args=(next_url,)))
        return HttpResponse(res)
    except ObjectDoesNotExist:
        res.say("ERROR: Question does not exist. Restarting.")
        res.redirect(reverse('feature_phone:landing'))
        return HttpResponse(res)

@csrf_exempt
def end(request):
    res = VoiceResponse()
    res.say('Thanks for particpating in Malasakit.')
    return HttpResponse(res)
