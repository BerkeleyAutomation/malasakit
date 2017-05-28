from __future__ import unicode_literals

import datetime

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils import timezone


class Translation(models.Model):
    """
    A `Translation` bundles a message with the language it is written in.
    """
    # Use the codes in the ISO 639-2 standard for the first entry.
    LANGUAGES = (
        ('ENG', 'English'),
        ('FIL', 'Filipino')
    )

    text = models.ForeignKey('Text', on_delete=models.CASCADE)
    language = models.CharField(max_length=3, choices=LANGUAGES)
    message = models.TextField()

    class Meta:
        unique_together = ('text', 'language')


class Text(models.Model):
    """
    A `Text` groups together equivalent translations.

    Any clients of the `Text` class can act language-agnostic.
    """
    tag = models.CharField(max_length=64)

    def get_translated_message(self, language):
        return self.translation_set.get(language=language).message

    class Meta:
        abstract = True


class Comment(Text):
    """
    A `Comment` is a user-generated response to a `QualitativeQuestion`.
    """
    question = models.ForeignKey('QualitativeQuestion', on_delete=models.CASCADE)
    author = models.ForeignKey('Respondent', on_delete=models.CASCADE)
    datetime = models.DateTimeField(auto_now_add=True)


class Templating(Text):
    """
    `Templating` is developer-generated text used for instructions and questions.
    """


class Rating(models.Model):
    NOT_RATED = -2
    SKIPPED = -1

    respondent = models.ForeignKey('Respondent', on_delete=models.CASCADE)
    datetime = models.DateTimeField(auto_now_add=True)
    score = models.SmallIntegerField(default=NOT_RATED)

    class Meta:
        abstract = True


class CommentRating(Rating):
    comment = models.ForeignKey('Comment', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('respondent', 'comment')


class QuantitativeQuestionRating(Rating):
    question = models.ForeignKey('QuantitativeQuestion', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('respondent', 'question')


class Question(models.Model):
    prompt = models.OneToOneField('Templating', on_delete=models.CASCADE)

    class Meta:
        abstract = True


class QualitativeQuestion(Question):
    prompt = models.ForeignKey('Templating', on_delete=models.CASCADE)

    @property
    def num_responses(self):
        return Comment.objects.filter(question=self).count()


class QuantitativeQuestion(Question):
    left_end_description = models.OneToOneField('Templating', on_delete=models.CASCADE)
    right_end_description = models.OneToOneField('Templating', on_delete=models.CASCADE)

    def select_ratings(self):
        return QuantitativeQuestionRating.objects.filter(question=self)

    @property
    def mean_score(self):
        pass

    @property
    def num_rated(self):
        excluded_ratings = [Rating.NOT_RATED, Rating.SKIPPED]
        return select_ratings().exclude(score__in=excluded_ratings).count()


class Respondent(models.Model):
    GENDERS = (
        ('M', 'Male'),
        ('F', 'Female')
    )

    age = models.PositiveSmallIntegerField(default=None, null=True, blank=True)
    barangay = models.CharField(max_length=512, default=None, null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDERS, default=None, null=True, blank=True)
    language = models.CharField(max_length=3, choices=Text.LANGUAGES, default='FIL')

    @property
    def num_rated(self):
        return Rating.objects.filter(respondent=self).count()
