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


class Response(models.Model):
    """
    A `Response` is an abstract model of user-generated data.
    """
    respondent = models.ForeignKey('Respondent', on_delete=models.CASCADE)
    datetime = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class Comment(Text, Response):
    """
    A `Comment` is a textual response to a `QualitativeQuestion`.
    """
    question = models.ForeignKey('QualitativeQuestion', on_delete=models.CASCADE)
    author = models.ForeignKey('Respondent', on_delete=models.CASCADE)
    datetime = models.DateTimeField(auto_now_add=True)


class Rating(Response):
    """
    A `Rating` is an abstract model of a numeric response.
    """
    NOT_RATED = -2
    SKIPPED = -1

    score = models.SmallIntegerField(default=NOT_RATED)

    class Meta:
        abstract = True


class QuantitativeQuestionRating(Rating):
    """
    A `QuantitativeQuestionRating` is a numeric response to a `QuantitativeQuestion`.
    """
    question = models.ForeignKey('QuantitativeQuestion', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('respondent', 'question')


class CommentRating(Rating):
    """
    A `CommentRating` is a numeric response to a `Comment`.
    """
    comment = models.ForeignKey('Comment', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('respondent', 'comment')


class Question(models.Model):
    prompt = models.OneToOneField('Text', on_delete=models.CASCADE)

    class Meta:
        abstract = True


class QualitativeQuestion(Question):
    @property
    def num_responses(self):
        return Comment.objects.filter(question=self).count()


class QuantitativeQuestion(Question):
    left_end_description = models.OneToOneField('Text', on_delete=models.CASCADE)
    right_end_description = models.OneToOneField('Text', on_delete=models.CASCADE)

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
