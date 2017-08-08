from __future__ import unicode_literals

import os

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext_lazy as _

from pcari.models import LANGUAGE_VALIDATOR


class RelatedModelMixin(models.Model):
    content_type = models.ForeignKey(
        ContentType,
        limit_choices_to=models.Q(app_label='pcari'),
        on_delete=models.CASCADE,
    )
    object_id = models.PositiveIntegerField(null=True, blank=True, default=None)
    related_object = GenericForeignKey()

    class Meta:
        abstract = True


class Instructions(models.Model):
    def generate_recording_path(instance, filename):
        model_name_plural = instance.__class__._meta.verbose_name_plural
        model_name_slug = model_name_plural.lower().replace(' ', '-')
        return '{0}/{1}'.format(model_name_slug, filename)

    recording = models.FileField(upload_to=generate_recording_path)
    tag = models.CharField(max_length=256, blank=True, default='')
    language = models.CharField(max_length=8, choices=settings.LANGUAGES,
                                blank=True, default='',
                                validators=[LANGUAGE_VALIDATOR])

    class Meta:
        verbose_name_plural = 'instructions'


class Question(Instructions, RelatedModelMixin):
    pass


class Response(models.Model):
    recording = models.FileField(upload_to='responses/')
    timestamp = models.DateTimeField(auto_now_add=True)
    respondent = models.ForeignKey('Respondent', on_delete=models.CASCADE)

    class Meta:
        abstract = True


class QuestionResponse(Response, RelatedModelMixin):
    question = models.ForeignKey('Question', on_delete=models.CASCADE)

    class Meta:
        unique_together = [
            ('content_type', 'object_id'),
            ('question', 'respondent'),
        ]


class CommentRating(Response):
    comment = models.ForeignKey('Response', on_delete=models.CASCADE)
    related_object = models.OneToOneField('pcari.CommentRating', null=True, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('comment', 'respondent')


class Respondent(models.Model):
    def make_recording_path_generator(field_name):
        def generate_recording_path(instance, filename):
            return 'respondent/{0}/{1}'.format(instance.pk, field_name)

    age = models.FileField(upload_to=make_recording_path_generator('age'))
    gender = models.FileField(upload_to=make_recording_path_generator('gender'))
    location = models.FileField(upload_to=make_recording_path_generator('location'))
    language = models.CharField(max_length=8, choices=settings.LANGUAGES,
                                blank=True, default='',
                                validators=[LANGUAGE_VALIDATOR])
    related_object = models.OneToOneField('pcari.Respondent', null=True, on_delete=models.CASCADE)
