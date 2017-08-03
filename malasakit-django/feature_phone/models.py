from __future__ import unicode_literals

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext_lazy as _

from pcari.models import LANGUAGE_VALIDATOR


class Recording(models.Model):
    language = models.CharField(max_length=8, choices=settings.LANGUAGES,
                                blank=True, default='',
                                validators=[LANGUAGE_VALIDATOR])
    timestamp = models.DateTimeField(auto_now_add=True)
    file = models.FileField()
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()
    content_object_field_name = models.CharField(max_length=100)
