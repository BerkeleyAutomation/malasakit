from __future__ import unicode_literals

import datetime

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils import timezone


class Response(models.Model):
    """
    A `Response` is an abstract model of user-generated data.

    Attributes:
        respondent: A reference to the user who made this `Response`.
        timestamp: The date and time at which this `Response` was submitted.
    """
    respondent = models.ForeignKey('Respondent', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class Comment(Response):
    """
    A `Comment` is a textual response to a `QualitativeQuestion`.

    Attributes:
        LANGUAGES: A tuple of pairs (tuples of size two), each of which has a
                   language code as the first entry and the language name as
                   the second. The three-letter language code should be taken
                   from the ISO 639-2 standard.
        language: A language code (see the `LANGAUGES` attribute).
        message: The text itself written in `language`.
        question: A reference to a `QualitativeQuestion`.
        flagged: A boolean indicating whether this comment was flagged for
                 further inspection.
        word_count: The number of words in the `message` (words are delimited
                    with contiguous whitespace).

    TODO: validate `language` on assignment

    Example usage:

    >>> respondent = Respondent()
    >>> question = QualitativeQuestion(prompt='How is the weather?')
    >>> comment = Comment(question=question, respondent=respondent,
    ...                   language='ENG', message='Not raining.')
    """
    LANGUAGES = (
        ('ENG', 'English'),
        ('FIL', 'Filipino')
    )

    question = models.ForeignKey('QualitativeQuestion', on_delete=models.CASCADE)
    language = models.CharField(max_length=3, choices=LANGUAGES)
    message = models.TextField()
    flagged = models.BooleanField(default=False)

    @property
    def word_count(self):
        return len(self.message.split())


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
    prompt = models.TextField()

    class Meta:
        abstract = True


class QualitativeQuestion(Question):
    @property
    def comments(self):
        return Comment.objects.filter(question=self)


class QuantitativeQuestion(Question):
    left_end_description = models.TextField()
    right_end_description = models.TextField()

    def select_ratings(self, answered=True):
        query = QuantitativeQuestionRating.objects.filter(question=self)
        if answered:
            excluded_ratings = [Rating.NOT_RATED, Rating.SKIPPED]
            return query.exclude(score__in=excluded_ratings)
        else:
            return query

    @property
    def mean_score(self):
        scores = list(select_ratings().all())
        return sum(scores)/len(scores)

    @property
    def num_ratings(self):
        return select_ratings().count()


class Respondent(models.Model):
    GENDERS = (
        ('M', 'Male'),
        ('F', 'Female')
    )

    age = models.PositiveSmallIntegerField(default=None, null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDERS, default=None, null=True, blank=True)
    # TODO: generalize location data
    barangay = models.CharField(max_length=512, default=None, null=True, blank=True)
    language = models.CharField(max_length=3, choices=Translation.LANGUAGES, default='FIL')

    @property
    def num_questions_rated(self):
        return QuantitativeQuestionRating.objects.filter(respondent=self).count()

    @property
    def num_comments_rated(self):
        return CommentRating.objects.filter(respondent=self).count()

    @property
    def comments_made(self):
        return Comment.objects.filter(respondent=self).all()
