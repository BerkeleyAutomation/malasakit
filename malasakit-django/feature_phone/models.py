from __future__ import unicode_literals

import os

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext_lazy as _

from pcari.models import LANGUAGE_VALIDATOR


class RelatedModelMixin(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(null=True, blank=True, default=None)
    content_object = GenericForeignKey()

    class Meta:
        abstract = True


class Recording(models.Model):
    language = models.CharField(max_length=8, choices=settings.LANGUAGES,
                                blank=True, default='',
                                validators=[LANGUAGE_VALIDATOR])
    file = models.FileField()

    class Meta:
        abstract = True


class QuestionRecording(Recording, RelatedModelMixin):
    tag = models.CharField(max_length=256, blank=True, default='')


class ResponseRecording(Recording, RelatedModelMixin):
    timestamp = models.DateTimeField(auto_now_add=True)
    question = QuestionRecording('QuestionRecording', on_delete=models.CASCADE)
    respondent = models.ForeignKey('Respondent', on_delete=models.CASCADE)


class Respondent(RelatedModelMixin):
    age = models.FileField()
    gender = models.FileField()
    location = models.FileField()
