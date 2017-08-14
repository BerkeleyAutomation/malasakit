from __future__ import unicode_literals

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _

from pcari.models import LANGUAGE_VALIDATOR


class RelatedObjectMixin(models.Model):
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
    model_name_plural = instance.__class__._meta.verbose_name_plural
    model_name_slug = model_name_plural.lower().replace(' ', '-')
    return '{0}/{1}'.format(model_name_slug, filename)


class Recording(models.Model):
    recording = models.FileField(upload_to=generate_recording_path)

    class Meta:
        abstract = True


class Instructions(Recording):
    MAX_TEXT_DISPLAY_LENGTH = 140

    text = models.TextField(blank=True, default='')
    tag = models.CharField(max_length=256, blank=True, default='')
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


class Question(Instructions, RelatedObjectMixin):
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
    timestamp = models.DateTimeField(auto_now_add=True)
    respondent = models.ForeignKey('Respondent', on_delete=models.CASCADE,
                                   related_name='responses')
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
