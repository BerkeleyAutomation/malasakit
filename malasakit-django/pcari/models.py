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
        timestamp: The date and time at which this `Response` was made.
    """
    respondent = models.ForeignKey('Respondent', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class Comment(Response):
    """
    A `Comment` is an open-ended text response to a `QualitativeQuestion`.

    Attributes:
        LANGUAGES: A tuple of pairs (tuples of size two), each of which has a
                   language code as the first entry and the language name as
                   the second. The three-letter language code should be taken
                   from the ISO 639-2 standard.
        question: A reference to a `QualitativeQuestion`.
        language: A language code (see the `LANGAUGES` attribute).
        message: The text itself written in `language`.
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

    class Meta:
        unique_together = ('respondent', 'question')


class Rating(Response):
    """
    A `Rating` is an abstract model of a numeric response.

    Attributes:
        NOT_RATED: A sentinel value assigned to a `Rating` that the user never
                   submitted (that is, a default value).
        SKIPPED: A sentinel value assigned to a `Rating` where the user
                 intentionally chose to decline rating a question or a comment.
        score: An integer that quantifies a rating. (No scale is provided, by
               design. Interpreting the `score` is the responsibility of
               clients of this model.)
    """
    NOT_RATED = -2
    SKIPPED = -1

    score = models.SmallIntegerField(default=NOT_RATED)

    class Meta:
        abstract = True


class QuantitativeQuestionRating(Rating):
    """
    A `QuantitativeQuestionRating` is a numeric response to a `QuantitativeQuestion`.

    Attributes:
        question: A reference to the `QuantitativeQuestion` this rating is in response to.
    """
    question = models.ForeignKey('QuantitativeQuestion', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('respondent', 'question')


class CommentRating(Rating):
    """
    A `CommentRating` is a numeric response to a `Comment`.

    Attributes:
        comment: A reference to the `Comment` this comment is in response to.
    """
    comment = models.ForeignKey('Comment', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('respondent', 'comment')


class Question(models.Model):
    """
    A `Question` models a prompt presented to the user that requires a response.

    Attributes:
        identifier: A unique string associated with each `Question`.
        prompt: The prompt in the primary language of the application.
    """
    identifier = models.CharField(max_length=16, primary_key=True)
    prompt = models.TextField(null=True, blank=True)


class QualitativeQuestion(Question):
    """
    A `QualitativeQuestion` is a `Question` that asks for a comment.
    """
    class Meta:
        proxy = True

    @property
    def comments(self):
        return Comment.objects.filter(question=self)


class QuantitativeQuestion(Question):
    """
    A `QuantitativeQuestion` is a `Question` that asks for a numeric rating.
    """
    class Meta:
        proxy = True

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
