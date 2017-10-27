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
    """ Landing page plays a welcome message. """
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
                 "numerical statements. You may either use your phone's keypad "
                 'or speak your response.')
    response.pause(1)
    return HttpResponse(response)


@csrf_exempt
@require_POST
def ask_quantitative_question(request):
    pass


"""
@csrf_exempt
def quantitative_questions(request):
    res = VoiceResponse()

    print "Respondent ID: %s" % request.session['respondent_id']

    user = Respondent.objects.get(id=request.session['respondent_id'])

    print "User: %s" % str(user)

    # query all questions for which user does NOT have a response
    # use related_object_type in RelatedObjectMixin

    # get all the quantitative question recordings
    questions = Question.objects.filter(related_object_type=ContentType.objects.get(
        app_label='pcari', model='quantitativequestion'))

    print "Questions: %s" % str(questions)

    # get all the questions that user has not made responses for

    not_answered = [q for q in questions if q not in [r.prompt for r in Response.objects.filter(respondent=user)]]

    print "Questions not answered: %s" % len(not_answered)

    if len(not_answered) == 0:
        # we have answered all quantitative questions! redirect to comment rating phase
        res.redirect(reverse('feature_phone:rate-comments'))
    else:
        # redirect back after recording
        res.play(not_answered[0].recording.url) # play the first unanswered question

        # initialize response for user. this response will be filled in at process_recording
        user_response = Response()
        user_response.respondent = user

        # this response is for a Question
        user_response.prompt = not_answered[0]

        # what quantitative question was this in response to?
        quant_q_model = not_answered[0].related_object

        user_response.related_object = QuantitativeQuestionRating(question=quant_q_model)

        user_response.save()

        # redirect back to quant question
        next_url = reverse('feature_phone:quantitative-questions')
        res.record(max_length=3, timeout=3,
                   action=reverse('feature_phone:process-recording', args=(next_url,)))

    return HttpResponse(res)
"""

@csrf_exempt
def process_recording(request, next_url):
    """
    After saving the recording, redirect to the next url.
    Probably want to pass in a newly-created Recording model, and then
    fill in the FileField here.

    """
    user = Respondent.objects.get(id=request.session['respondent_id'])

    # User will have a Response without a recording field that was just created.
    user_responses = Response.objects.filter(respondent=user)
    empty_response = None
    for r in user_responses:
        print r
        if not r.recording:
            empty_response = r

    # Recording might not be available yet, use recordingStatusCallback
    # while rendering Record verb.
    # https://www.twilio.com/docs/api/twiml/record#attributes-recording-status-callback

    recording_url = request.POST.get('RecordingUrl', 'NOT AVAILABLE')

    with TemporaryFile() as f:
        f.write(requests.get(recording_url).content)
        empty_response.recording = File(f, name="%s.mp3" % (empty_response.id))
        empty_response.save()

    res = VoiceResponse()

    # SAVE AUDIO RESPONSE HERE

    res.say("Recording saved.")

    res.redirect(next_url)
    return HttpResponse(res)

@csrf_exempt
def rate_comments(request):
    """
    Can the user keep rating? Not sure. Let's assume no for now.
    """

    # How many comment ratings has the user produced?
    user = Respondent.objects.get(id=request.session['respondent_id'])

    num_rated = len(Response.objects.filter(respondent=user,
                            prompt_type=ContentType.objects.get(
                                      app_label='feature_phone',
                                      model='response'
                                  )))

    # cast again

    NUM_COMMENTS = 2 # max number of comments to rate

    res = VoiceResponse()

    ##### REPLACE WITH SAMPLING CODE #####
    comments = Response.objects.filter(related_object_type=ContentType.objects.get(
        app_label='pcari',
        model='comment'
    ))
    # get all responses that are supposed to be linked to pcari.comments

    print "Comments: %s" % str(comments)


    if len(comments) < NUM_COMMENTS or num_rated >= NUM_COMMENTS:
        # not enough comments or enough have been rated? move to qualittative questions
        res.redirect(reverse('feature_phone:qualitative-questions'))
    elif num_rated < NUM_COMMENTS:
        # more comments to rate. so we'll redirect back here
        next_url = reverse('feature_phone:rate-comments')

        comment = random.sample(comments, 1)[0]
        res.say("This user made a suggestion. Please rate it from 0 to 9.")
        res.pause(1)
        res.play(comment.recording.url)

        res.record(max_length=3, timeout=3,
               action=reverse('feature_phone:process-recording', args=(next_url,)))

        # initialize response for user. this response will be filled in at process_recording
        user_response = Response()
        user_response.respondent = user

        user_response.prompt = comment
        user_response.related_object_type = ContentType.objects.get(app_label='pcari',
                                                                    model='commentrating')
        num_rated += 1

    return HttpResponse(res)

@csrf_exempt
def qualitative_questions(request):
    """Plays qualitative question. Essentially the same as quantitative_questions but
    with longer recording verbs."""
    res = VoiceResponse()

    user = Respondent.objects.get(id=request.session['respondent_id'])

    # query all questions for which user does NOT have a response
    # use related_object_type in RelatedObjectMixin

    # get all the quantitative question recordings
    questions = Question.objects.filter(related_object_type=ContentType.objects.get(
        app_label='pcari', model='qualitativequestion'))

    print "Questions: %s" % str(questions)

    # get all the questions that user has not made responses for

    not_answered = [q for q in questions if q not in [r.prompt for r in Response.objects.filter(respondent=user)]]

    print "Questions not answered: %s" % len(not_answered)

    if len(not_answered) == 0:
        # we have answered all quantitative questions! redirect to comment rating phase
        res.redirect(reverse('feature_phone:end'))
    else:
        # redirect back after recording
        res.play(not_answered[0].recording.url) # play the first unanswered question

        # initialize response for user. this response will be filled in at process_recording
        user_response = Response()
        user_response.respondent = user

        # this response is for a Question
        user_response.prompt = not_answered[0]

        # what quantitative question was this in response to?
        qual_q_model = not_answered[0].related_object

        user_response.related_object = Comment(question=qual_q_model)

        user_response.save()

        # redirect back to quant question
        next_url = reverse('feature_phone:qualitative-questions')
        res.record(max_length=10, timeout=10,
                   action=reverse('feature_phone:process-recording', args=(next_url,)))

    return HttpResponse(res)



@csrf_exempt
def end(request):
    res = VoiceResponse()
    res.say('Thanks for particpating in Malasakit.')
    return HttpResponse(res)
