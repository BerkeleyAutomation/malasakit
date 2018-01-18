"""
Model definitions.

This module defines how information used by Malasakit is structured and how the
Python layer interfaces with a database.

The Question and Response models used in v2.0 are linked to their corresponding quantitative
question, qualitative question, and response objects from v1.25 through the RelatedObjectMixin.

References:
    * `Django Model Reference <https://docs.djangoproject.com/en/dev/topics/db/models/>`_
    * `Django Field Reference <https://docs.djangoproject.com/en/dev/ref/models/fields/>`_
    * `QuerySet API <https://docs.djangoproject.com/en/dev/ref/models/querysets/>`_
    * `The contenttypes framework
       <https://docs.djangoproject.com/en/dev/ref/contrib/contenttypes/>`_
"""

from __future__ import unicode_literals

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _

from pcari.models import LANGUAGE_VALIDATOR


class RelatedObjectMixin(models.Model):
    """
    The ``RelatedObjectMixin`` provides models access to their corresponding linked
    database objects from PCARI v1.25 models.

    To use this mixin on a model, have the model inherit from this class after
    it inherits from :class:`django.db.models.Model` (or some subclass of
    ``Model``). It cannot be inherited on its own, and must be included via multiple
    inheritance to any v2 model.

    Attributes:
        related_object_type: The type of the linked v1.25 object.
        related_object_id: The id of the linked v1.25 object.
        related_object: The linked v1.25 object.
    """
    related_object_type = models.ForeignKey(
        ContentType,
        limit_choices_to=models.Q(app_label='pcari'),
        on_delete=models.CASCADE,
        related_name='+',
    )
    related_object_id = models.PositiveIntegerField(null=True, blank=True,
                                                    default=None,
                                                    verbose_name=_('Related object ID'))
    related_object = GenericForeignKey('related_object_type',
                                       'related_object_id')

    class Meta:
        abstract = True


def generate_recording_path(instance, filename):
    """
    Create a path in the file tree to which the recording is stored.

    Args:
        instance: A recording object.
        filename (String): The filename for the recording.

    Returns:
        String: A path, containing a folder and a directory, to which the recording
        is stored.
    """
    model_name_plural = instance.__class__._meta.verbose_name_plural
    model_name_slug = model_name_plural.lower().replace(' ', '-')
    return '{0}/{1}'.format(model_name_slug, filename)


class Recording(models.Model):
    """
    A Recording is an abstract model of a recording

    Attributes:
        recording: Contains the path to which the recording is stored on disk.
        text (str): The text content of the ``Recording``.
    """
    recording = models.FileField(upload_to=generate_recording_path)
    text = models.TextField(blank=True, default='')

    class Meta:
        abstract = True


class Instructions(Recording):
    """
    An ``Instruction`` is a string of text that will be spoken to a caller.

    Attributes:
        key (str): A unique identifier for this ``Instruction``.
        language (str): The language the ``Instruction`` is written in.
    """
    MAX_TEXT_DISPLAY_LENGTH = 140

    key = models.SlugField()
    language = models.CharField(max_length=8, choices=settings.LANGUAGES,
                                blank=True, default='',
                                validators=[LANGUAGE_VALIDATOR])

    def __unicode__(self):
        text = self.text
        if text is not None and text.strip() and len(text) > self.MAX_TEXT_DISPLAY_LENGTH:
            text = text[:self.MAX_TEXT_DISPLAY_LENGTH] + ' ...'
        return 'Instructional recording: "{0}"'.format(text)

    class Meta:
        verbose_name_plural = 'instructions'
        unique_together = ('key', 'language')


class Question(Instructions, RelatedObjectMixin):
    """
    A ``Question`` is a type of Instruction that is specifically spoken to the caller during the
    quantitative and qualitative question part of the call.
    """
    # pylint: disable=model-no-explicit-unicode

    def validate_unique(self, exclude=None):
        super(Question, self).clean()
        fields = {'related_object_type', 'related_object_id', 'language'}
        if not set(exclude) & fields:
            try:
                constraints = {field: getattr(self, field) for field in fields}
                question = Question.objects.get(**constraints)
                if question != self:
                    raise ValueError
            except Question.DoesNotExist:
                return
            except (ValueError, Question.MultipleObjectsReturned):
                raise ValidationError(_('question fails uniqueness constraint '
                                        'on combined files: %(fields)s'),
                                      {'fields': ', '.join(map(repr, fields))})


class Response(Recording, RelatedObjectMixin):
    """
    A ``Response`` is a Recording of the caller's answer to the prompted Questions.

    Attributes:
        timestamp (datetime.datetime): When this Response was made.
        respondent: The Respondent who made this Response.
        url (str): The voice response's Twilio URL.
        prompt_type: The type of the prompt which this Response addressed.
        prompt_id: The ID of the prompt which this Response addressed.
        prompt: The prompt which this Response addressed.
    """
    timestamp = models.DateTimeField(auto_now_add=True)
    respondent = models.ForeignKey('Respondent', on_delete=models.CASCADE,
                                   related_name='responses')
    url = models.URLField(blank=True, default='', verbose_name='URL')
    prompt_type = models.ForeignKey(
        ContentType,
        limit_choices_to=models.Q(app_label='feature_phone', model='question')
        | models.Q(app_label='feature_phone', model='response'),
        on_delete=models.CASCADE,
        related_name='+',
    )
    prompt_id = models.PositiveIntegerField(null=True, blank=True, default=None,
                                            verbose_name=_('Prompt ID'))
    prompt = GenericForeignKey('prompt_type', 'prompt_id')

    def __unicode__(self):
        return 'Voice response to instance {0} of "{1}.{2}"'.format(
            self.related_object_id,
            self.related_object_type.app_label,
            self.related_object_type.model,
        )

    class Meta:
        unique_together = [
            ('related_object_type', 'related_object_id'),
            ('prompt_type', 'prompt_id', 'respondent'),
        ]


class Respondent(models.Model):
    """
    A ``Respondent`` represents a one-time participant in the survey.

    Attributes:
        call_sid: A unique identifier for the call made by this respondent.
            Generated by Twilio.
        age: The age of the respondent in years.
        gender: The gender of the respondent
        location: The respondent's residence. (In the particular context of
            the Philippines, this field should contain the respondent's province,
            city or municipality, and barangay.)
        language: The language preferred by this respondent. Selected
            from :attr:`pcari.models.LANGUAGES`.
        related_object: Ties the respondent with the corresponding database
            object from v1.25
    """
    call_sid = models.CharField(max_length=64, unique=True)
    age = models.FileField(upload_to='respondent/age/', null=True, blank=True,
                           default=None)
    gender = models.FileField(upload_to='respondent/gender/', null=True,
                              blank=True, default=None)
    location = models.FileField(upload_to='respondent/location/', null=True,
                                blank=True, default=None)
    language = models.CharField(max_length=8, choices=settings.LANGUAGES,
                                blank=True, default='',
                                validators=[LANGUAGE_VALIDATOR])
    related_object = models.OneToOneField('pcari.Respondent', null=True,
                                          blank=True, default=None,
                                          on_delete=models.CASCADE,
                                          related_name='related_object')

    def __unicode__(self):
        return 'Respondent {0}'.format(self.pk)
