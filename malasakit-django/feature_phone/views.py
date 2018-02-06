"""
This module defines the application's views, which are needed to render pages.

"Pages" are generated in TwiML (Twilio Markup Language) for Twilio to play
desired audio.

See https://www.twilio.com/docs/api/twiml and
https://twilio.github.io/twilio-python/6.5.0/twiml/
"""

import logging
import os
from string import digits
import time
from urllib2 import urlopen

from django.core.files.base import ContentFile
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import get_language
import numpy as np
from twilio.twiml.voice_response import VoiceResponse, Gather

from feature_phone.models import Respondent, Question, Response, Instructions
from pcari import models as web_models
from pcari.templatetags.localize_url import localize_url

REPEAT_DIGIT = '*'
SKIP_DIGIT = '#'
LOGGER = logging.getLogger('pcari')


def play_recording(action, recording):
    """
    Play a voice recording, either from a file or using speech synthesis.

    Arguments:
        action: A Twilio object that supports `Say` and `Play` verbs.
        recording: A `Recording` instance.
    """
    if recording.recording.name:
        url = os.path.join(settings.MEDIA_URL, recording.recording.name)
        action.play(url)
    elif recording.text:
        action.say(recording.text)


def speak(action, instruction_keys, pause_duration=0):
    """
    Play a list of instructions.

    Arguments:
        action: A Twilio object that supports `Say`, `Play`, and `Pause` verbs.
        instruction_keys (list): A list of instruction keys.
        pause_duration (float): The delay between instructions in seconds.

    Note:
        To minimize possibly unwanted latency, a pause does not follow the last
        instruction spoken.
    """
    try:
        instructions = [Instructions.objects.get(key=key, language=get_language())
                        for key in instruction_keys]
    except Instructions.DoesNotExist:
        LOGGER.warn('Could not play all instructions: %s', repr(instruction_keys))
        return

    for index, instruction in enumerate(instructions):
        play_recording(action, instruction)
        if index < len(instructions) - 1 and pause_duration > 0:
            action.pause(pause_duration)


@method_decorator(csrf_exempt, name='dispatch')
class PromptView(View):
    """
    Present a question to the listener, and gather any desired inputs.

    Attributes:
        submit_view (str): The name of the view the Twilio client yields
            control to after this prompt. Any data recorded arrives as POST
            parameters `Digits` or `RecordingUrl`.
        prompts (list): A list of keys of instructions to read.
        accept_keypress (bool): A flag that determines whether this view should
            accept a single keypress as input.
        timeout (float): The maximum amount of time in seconds the Twilio
            client will wait for without input from the listener before moving
            to :attr:`submit_view`.
        accept_speech (bool): A flag that determines whether this view should
            accept spoken recordings as input.
        play_beep (bool): A flag that determines whether the Twilio client
            should play a beep tone to signal the start of a recording period.
        recording_max_duration (float): The maximum amount of time a recording
            may take.
        recording_callback (str): The name of the view that will handle actions
            made after Twilio finalizes the recording.

    Notes:
        Keypresses made while a prompt plays will interrupt the playback, while
        speech will not. Only speech made after the prompt plays will be
        recorded.
    """
    submit_view = None
    prompts = []
    accept_keypress = True
    timeout = 4
    accept_speech = False
    play_beep = True
    recording_max_duration = 60
    recording_callback = None
    http_method_names = ['post']

    def ask(self, request, action):
        # pylint: disable=unused-argument
        if self.prompts:
            speak(action, self.prompts)
        else:
            raise NotImplementedError

    def fallback(self, voice_response):
        pass

    def post(self, request):
        """ Serve the Twilio client directions for collecting input. """
        voice_response = VoiceResponse()
        if self.accept_keypress:
            keypress_timeout = 0 if self.accept_speech else self.timeout
            gather = Gather(input='dtmf', action=reverse(self.submit_view),
                            finish_on_key='', timeout=keypress_timeout,
                            num_digits=1)
            self.ask(request, gather)
            voice_response.append(gather)
        else:
            self.ask(request, voice_response)
        if self.accept_speech:
            end_keys = SKIP_DIGIT + REPEAT_DIGIT + digits if self.accept_keypress else ''
            voice_response.record(action=reverse(self.submit_view),
                                  play_beep=self.play_beep, timeout=self.timeout,
                                  max_length=self.recording_max_duration,
                                  recording_status_callback=reverse(self.recording_callback),
                                  finish_on_key=end_keys)
        self.fallback(voice_response)
        voice_response.redirect(reverse(self.submit_view))
        return HttpResponse(voice_response, content_type='application/xml')


@method_decorator(csrf_exempt, name='dispatch')
class SaveView(View):
    """
    Process incoming data, then redirect the listener to another view.
    """
    next_view = None
    http_method_names = ['post']

    def save(self, request, voice_response):
        pass

    def post(self, request):
        """ Handle incoming input. """
        voice_response = VoiceResponse()
        self.save(request, voice_response)
        voice_response.redirect(reverse(self.next_view))
        return HttpResponse(voice_response, content_type='application/xml')


def get_respondent(session, pk_key='respondent-pk'):
    return Respondent.objects.get(pk=session[pk_key])


class PromptLanguageView(PromptView):
    """ Ask the listener for their preferred language. """
    submit_view = 'feature-phone:save-language'
    accept_keypress = True
    accept_speech = False

    def ask(self, request, action):
        play_recording(action, Instructions.objects.get(key='welcome', language='en'))
        play_recording(action, Instructions.objects.get(key='language-selection', language='en'))
        for key in sorted(SaveLanguageView.key_to_language.keys()):
            language = SaveLanguageView.key_to_language[key]
            language_codes_in_use = [code_and_name[0] for code_and_name in settings.LANGUAGES]
            if language != 'en' and language in language_codes_in_use:
                instruction = Instructions.objects.get(key='language-selection', language=language)
                play_recording(action, instruction)


class SaveLanguageView(SaveView):
    """ Save listener language selections, and redirect them accordingly. """
    next_view = 'feature-phone:prompt-irb-notice'
    key_to_language = {
        '1': 'en',
        '2': 'tl',
        '3': 'ceb',
        '4': 'ilo',
    }

    def save(self, request, voice_response):
        digit = request.POST.get('Digits')
        language = self.key_to_language.get(digit, settings.LANGUAGE_CODE)
        language_codes_in_use = [code_and_name[0] for code_and_name in settings.LANGUAGES]
        if language not in language_codes_in_use:
            language = 'en'

        # pylint: disable=no-member
        related_object = web_models.Respondent.objects.create()
        respondent = Respondent.objects.create(
            related_object_id=related_object.id,
            call_sid=request.POST['CallSid'],
            language=language,
        )
        request.session['respondent-pk'] = respondent.pk

        LOGGER.info("Respondent %d selected language '%s'", respondent.pk, language)
        return language

    def post(self, request):
        voice_response = VoiceResponse()
        language = self.save(request, voice_response)
        voice_response.redirect(localize_url(reverse(self.next_view), language))
        return HttpResponse(voice_response, content_type='application/xml')


class PromptIRBNoticeView(PromptView):
    """ Present an IRB notice to listeners, and allow them to opt-out. """
    submit_view = 'feature-phone:verify-irb-notice'
    prompts = ['introduction', 'irb-notice', 'irb-notice-prompt']
    accept_keypress = True
    accept_speech = False


class VerifyIRBNoticeView(SaveView):
    """ Hang up if the listener does not accept the IRB, or continue otherwise. """
    next_view = 'feature-phone:prompt-gender'
    accept_irb_key = '1'

    def post(self, request):
        accepted = request.POST.get('Digits') == self.accept_irb_key
        respondent = get_respondent(request.session)
        if not accepted:
            voice_response = VoiceResponse()
            speak(voice_response, ['irb-notice-exit'])
            voice_response.hangup()
            LOGGER.debug('Respondent %d declined IRB notice', respondent.pk)
            return HttpResponse(voice_response, content_type='application/xml')
        LOGGER.debug('Respondent %d accepted IRB notice', respondent.pk)
        return super(VerifyIRBNoticeView, self).post(request)


class PromptGenderView(PromptView):
    """ Ask listeners for their gender. """
    submit_view = 'feature-phone:save-gender'
    prompts = ['gender-prompt']
    accept_keypress = True
    accept_speech = False


class SaveGenderView(SaveView):
    """ Save responses to the gender question. """
    next_view = 'feature-phone:prompt-age'
    key_to_gender = {
        '1': 'M',
        '2': 'F',
    }

    def save(self, request, voice_response):
        respondent = get_respondent(request.session)
        gender = self.key_to_gender.get(request.POST.get('Digits'))
        if respondent.related_object and gender:
            respondent.related_object.gender = gender
            respondent.related_object.save()
            LOGGER.debug('Respondent %d selected "%s" to gender question', respondent.pk, gender)
        else:
            LOGGER.debug('Respondent %d skipped gender question', respondent.pk)


class PromptAgeView(PromptView):
    """ Ask listeners for their age. """
    submit_view = 'feature-phone:prompt-barangay'
    prompts = ['age-prompt']
    accept_keypress = False
    accept_speech = True
    recording_callback = 'feature-phone:download-age'


@csrf_exempt
@require_POST
def download_age_recording(request):
    """ Download recordings of listeners stating their ages. """
    url = request.POST.get('RecordingUrl')
    respondent = Respondent.objects.get(call_sid=request.POST['CallSid'])
    if url:
        fetch_recording(respondent.age, url)
        LOGGER.debug('Downloaded age recording for respondent %d', respondent.pk)
    else:
        LOGGER.warn('Callback missing "RecordingUrl" parameter for age')
    return HttpResponse(content_type='application/xml')


class PromptBarangayView(PromptView):
    """ Ask listeners for their barangay. """
    submit_view = 'feature-phone:quantitative-question-instructions'
    prompts = ['barangay-prompt']
    accept_keypress = False
    accept_speech = True
    recording_callback = 'feature-phone:download-barangay'


@csrf_exempt
@require_POST
def download_barangay_recording(request):
    """ Download recordings of listeners stating their barangays. """
    url = request.POST.get('RecordingUrl')
    respondent = Respondent.objects.get(call_sid=request.POST['CallSid'])
    if url:
        fetch_recording(respondent.location, url)
        LOGGER.debug('Downloaded barangay recording for respondent %d', respondent.pk)
    else:
        LOGGER.warn('Callback missing "RecordingUrl" parameter for barangay')
    return HttpResponse(content_type='application/xml')


class QuantiativeQuestionInstructionsView(PromptView):
    """ Explain the quantitative question section, and initialize session data. """
    submit_view = 'feature-phone:prompt-quantitative-question'
    accept_keypress = True
    accept_speech = False
    timeout = 0
    prompts = ['quantitative-question-instructions', 'quantitative-question-reminder']

    def ask(self, request, action):
        speak(action, self.prompts)
        request.session['index'] = 0
        question_type = ContentType.objects.get_for_model(web_models.QuantitativeQuestion)
        request.session['obj-keys'] = fetch_question_pks(question_type)


class PromptQuantitativeQuestionView(PromptView):
    """ Ask a quantitative question. """
    submit_view = 'feature-phone:save-quantitative-rating'
    accept_keypress = True
    accept_speech = True
    recording_max_duration = 15
    recording_callback = 'feature-phone:download-recording'

    def ask(self, request, action):
        question_pk = request.session['obj-keys'][request.session['index']]
        play_recording(action, Question.objects.get(pk=question_pk))

    def post(self, request):
        if request.session['index'] >= len(request.session['obj-keys']):
            voice_response = VoiceResponse()
            voice_response.redirect(reverse('feature-phone:comment-rating-instructions'))
            return HttpResponse(voice_response, content_type='application/xml')
        return super(PromptQuantitativeQuestionView, self).post(request)


class SaveQuantitativeRatingView(SaveView):
    """ Record a rating to a quantitative question. """
    next_view = 'feature-phone:prompt-quantitative-question'

    def save(self, request, voice_response):
        digit = request.POST.get('Digits', '')
        if digit == REPEAT_DIGIT:
            return

        question_pk = request.session['obj-keys'][request.session['index']]
        try:
            question = Question.objects.get(pk=question_pk)
        except Question.DoesNotExist:
            LOGGER.warn('Question %d does not exist', question_pk)
            return

        respondent = get_respondent(request.session)
        # pylint: disable=no-member
        rating = web_models.QuantitativeQuestionRating.objects.create(
            question=question.related_object,
            respondent=respondent.related_object,
        )
        response = make_response(respondent, question, rating)
        transcribe_rating(response, digit)
        response.url = request.POST.get('RecordingUrl', '')
        response.save()

        LOGGER.debug('Respondent %d answered quantitative question %d', respondent.pk, question.pk)
        request.session['index'] += 1

    def post(self, request):
        if request.POST.get('Digits') == 'hangup':
            LOGGER.debug('Respondent %d hung up', get_respondent(request.session).pk)
            return HttpResponse(content_type='application/xml')
        return super(SaveQuantitativeRatingView, self).post(request)


class CommentRatingInstructions(PromptView):
    """ Explain the peer evaluation section, and select the suggestions to be presented. """
    submit_view = 'feature-phone:prompt-comment'
    accept_keypress = True
    accept_speech = False
    timeout = 0
    prompts = ['comment-rating-instructions']

    def ask(self, request, action):
        speak(action, self.prompts)
        request.session['index'] = 0
        request.session['obj-keys'] = select_comment_pks()


class PromptCommentView(PromptView):
    """ Play back a suggestion to the listener. """
    submit_view = 'feature-phone:save-comment-rating'
    accept_keypress = True
    accept_speech = True
    recording_max_duration = 15
    recording_callback = 'feature-phone:download-recording'

    def ask(self, request, action):
        comment_pk = request.session['obj-keys'][request.session['index']]
        try:
            comment = Response.objects.get(related_object_id=comment_pk)
            play_recording(action, comment)
        except Response.DoesNotExist:
            comment = web_models.Comment.objects.get(pk=comment_pk)
            action.say(comment.message)

    def post(self, request):
        if request.session['index'] >= len(request.session['obj-keys']):
            voice_response = VoiceResponse()
            voice_response.redirect(reverse('feature-phone:qualitative-question-instructions'))
            return HttpResponse(voice_response, content_type='application/xml')
        return super(PromptCommentView, self).post(request)


class SaveCommentRatingView(SaveView):
    """ Recording a rating of a suggestion. """
    next_view = 'feature-phone:prompt-comment'

    def save(self, request, voice_response):
        digit = request.POST.get('Digits', '')
        if digit == REPEAT_DIGIT:
            return

        comment_pk = request.session['obj-keys'][request.session['index']]
        comment = web_models.Comment.objects.get(pk=comment_pk)
        respondent = get_respondent(request.session)
        comment, _ = Response.objects.get_or_create(related_object_id=comment.pk, defaults={
            'respondent': respondent,
            'prompt_type': ContentType.objects.get_for_model(Question),
            'related_object_type': ContentType.objects.get_for_model(web_models.Comment),
        })

        # pylint: disable=no-member
        rating = web_models.CommentRating.objects.create(
            comment=comment.related_object,
            respondent=respondent.related_object,
        )
        response = make_response(respondent, comment, rating)
        transcribe_rating(response, digit)
        response.url = request.POST['RecordingUrl']
        response.save()

        LOGGER.debug('Respondent %d rated comment %d', respondent.pk, comment.pk)
        request.session['index'] += 1

    def post(self, request):
        if request.POST.get('Digits') == 'hangup':
            LOGGER.debug('Respondent %d hung up', get_respondent(request.session).pk)
            return HttpResponse(content_type='application/xml')
        return super(SaveCommentRatingView, self).post(request)


class QualitativeQuestionInstructionsView(PromptView):
    """ Expalin the qualitative question section, and initialize session data. """
    submit_view = 'feature-phone:prompt-qualitative-question'
    accept_keypress = True
    accept_speech = False
    timeout = 0
    prompts = ['qualitative-question-instructions']

    def ask(self, request, action):
        speak(action, self.prompts)
        request.session['index'] = 0
        question_type = ContentType.objects.get_for_model(web_models.QualitativeQuestion)
        request.session['obj-keys'] = fetch_question_pks(question_type)


class PromptQualitativeQuestionView(PromptView):
    """ Ask the listener for a suggestion. """
    submit_view = 'feature-phone:confirm-comment'
    accept_keypress = True
    accept_speech = True
    recording_callback = 'feature-phone:download-recording'

    def ask(self, request, action):
        question_pk = request.session['obj-keys'][request.session['index']]
        question = Question.objects.get(pk=question_pk)
        play_recording(action, question)

    def post(self, request):
        if request.session['index'] >= len(request.session['obj-keys']):
            voice_response = VoiceResponse()
            voice_response.redirect(reverse('feature-phone:end'))
            return HttpResponse(voice_response, content_type='application/xml')
        return super(PromptQualitativeQuestionView, self).post(request)


class ConfirmCommentView(PromptView):
    """
    Ask the listener to confirm they are satisfied with their suggestion.

    Note:
        Since the raw suggestions are played back to other listeners, it is
        important to ensure listeners can re-record their suggestions. However,
        this only happens once (otherwise, listeners may feel compelled to
        unnecessarily polish their suggestions).
    """
    submit_view = 'feature-phone:save-comment'
    prompts = ['qualitative-question-confirm']
    accept_keypress = True
    accept_speech = False

    def post(self, request):
        question_pk = request.session['obj-keys'][request.session['index']]
        question = Question.objects.get(pk=question_pk)
        respondent = get_respondent(request.session)

        if request.POST.get('Digits') == 'hangup':
            return HttpResponse(content_type='application/xml')
        elif request.POST.get('Digits') == SKIP_DIGIT or request.session.get('repeat'):
            if request.session.get('repeat'):
                response = Response.objects.get(
                    respondent=respondent,
                    prompt_type=ContentType.objects.get_for_model(Question),
                    prompt_id=question_pk,
                )
                response.url = request.POST['RecordingUrl']
                response.save()
            request.session['index'] += 1
            request.session['repeat'] = False
            voice_response = VoiceResponse()
            voice_response.redirect(reverse('feature-phone:prompt-qualitative-question'))
            return HttpResponse(voice_response, content_type='application/xml')
        else:
            comment = web_models.Comment.objects.create(
                question=question.related_object,
                respondent=respondent.related_object,
                language=get_language(),
            )
            response = make_response(respondent, question, comment)
            response.url = request.POST['RecordingUrl']
            response.save()
        return super(ConfirmCommentView, self).post(request)


class SaveCommentView(SaveView):
    """ Handle responses to the suggestion confirmation prompt. """
    next_view = 'feature-phone:prompt-qualitative-question'
    rerecord_key = '1'

    def save(self, request, voice_response):
        if request.POST.get('Digits', '') != self.rerecord_key:
            request.session['index'] += 1
            request.session['repeat'] = False
        else:
            request.session['repeat'] = True


@csrf_exempt
@require_POST
def end(request):
    """ Clean up local session data, thank the listener, and hang up. """
    for key in ['respondent-pk', 'index', 'obj-keys', 'repeat']:
        if key in request.session:
            del request.session[key]

    voice_response = VoiceResponse()
    speak(voice_response, ['end'])
    voice_response.hangup()
    return HttpResponse(voice_response, content_type='application/xml')


def select_comment_pks(num_to_select=2):
    """ Select comments to play to a listener. """
    comments = web_models.Comment.objects.filter(
        language=get_language() or settings.LANGUAGE_CODE,
    ).exclude(message='')
    comment_pks, standard_errors = zip(*comments.values_list('pk', 'score_sem'))
    if not comment_pks:
        return []

    standard_errors = np.array([
        (std_error if std_error is not None else settings.DEFAULT_STANDARD_ERROR)
        for std_error in standard_errors
    ])
    probabilities = standard_errors/np.sum(standard_errors)
    # pylint: disable=no-member
    return list(np.random.choice(comment_pks, size=num_to_select, replace=False,
                                 p=probabilities))


def fetch_question_pks(question_type, include_orphans=False):
    """
    Fetch all primary keys (in order) of a given question type.

    Arguments:
        question_type: A `ContentType` instance of the question model.
        include_orphans (bool): A flag that indicates whether the query should
            return feature phone-only questions.
    """
    questions = Question.objects.filter(related_object_type=question_type,
                                        language=get_language())
    # Need to use a list because the filter needs to access a field of `related_object`
    questions = [question for question in questions if question.related_object is None
                 and include_orphans or question.related_object.active]
    def key(question):
        """ Sort questions such that orphaned questions or those with no order given are last. """
        if question.related_object and question.related_object.order is not None:
            return question.related_object.order
        return float('inf')
    questions.sort(key=key)
    return [question.pk for question in questions]


def fetch_recording(file_field, url):
    """ Download a recording from the given URL as a file field value. """
    response = urlopen(url)
    response_buffer = ContentFile(response.read())
    file_field.save(os.path.basename(url), response_buffer, save=True)


def make_response(respondent, prompt, related_object):
    """ Make a feature phone response. """
    return Response.objects.create(
        respondent=respondent,
        prompt_type=ContentType.objects.get_for_model(prompt.__class__),
        prompt_id=prompt.pk,
        related_object_type=ContentType.objects.get_for_model(related_object.__class__),
        related_object_id=related_object.pk,
    )


def transcribe_rating(response, text=''):
    """ Transcribe a keypress to its related web-facing model. """
    response.text = text
    response.save()

    rating = response.related_object
    if rating:
        if response.text.isdigit():
            score = int(response.text)
            if (not hasattr(rating, 'question') or
                    rating.question.min_score <= score <= rating.question.max_score):
                rating.score = score
                rating.save()
        elif response.text == SKIP_DIGIT:
            rating.score = rating.SKIPPED
            rating.save()


@csrf_exempt
@require_POST
def download_recording(request):
    """ Download a recording for a `Response` instance, which must have had its URL set.  """
    if 'RecordingUrl' in request.POST:
        try:
            url = request.POST['RecordingUrl']
            if url:
                time.sleep(3)  # Ensure the response's URL attribute has been set
                voice_response = Response.objects.get(url=url)
                fetch_recording(voice_response.recording, url)
                voice_response.save()
        except Response.DoesNotExist:
            LOGGER.warn('Response with recording URL %s does not exist', url)
    else:
        LOGGER.warn('Parameter "RecordingUrl" not passed to recording download callback')
    return HttpResponse(content_type='application/xml')


@csrf_exempt
@require_POST
def error(request):
    """
    Read an error message to a listener, and gracefully exit.

    This should never happen. Uses a minimal `Say` verb to avoid points of failure.
    """
    # pylint: disable=unused-argument
    voice_response = VoiceResponse()
    voice_response.say('Our apologies: Malasakit is experiencing issues at this time. '
                       'Please try again momentarily.')
    voice_response.hangup()
    LOGGER.error('Critical error')
    return HttpResponse(voice_response, content_type='application/xml')
