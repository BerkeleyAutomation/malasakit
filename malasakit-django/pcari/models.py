"""
This module defines the structure of the data.

Attributes:
    LANGUAGES: A tuple of pairs (tuples of size two), each of which has a
               language code as the first entry and the language name as
               the second. The three-letter language code should be taken
               from the ISO 639-2 standard.
"""

from __future__ import unicode_literals

# Public-facing models (parent models are excluded)
__all__ = ['Comment', 'QuantitativeQuestionRating', 'CommentRating',
           'QualitativeQuestion', 'QuantitativeQuestion', 'Respondent']

from django.db import models


LANGUAGES = (
    ('ENG', 'English'),
    ('FIL', 'Filipino')
)


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
        question: A reference to a `QualitativeQuestion`.
        language: A language code (see this module's `LANGAUGES` attribute).
        message: The text itself written in `language`.
        flagged: A boolean indicating whether this comment was flagged for
                 further inspection.
        tag: A short string that summarizes this comment's message. (This field
             is not user-generated.)
        word_count: The number of words in the `message` (words are delimited
                    with contiguous whitespace).

    Example usage:

    >>> respondent = Respondent()
    >>> question = QualitativeQuestion(prompt='How is the weather?')
    >>> comment = Comment(question=question, respondent=respondent,
    ...                   language='ENG', message='Not raining.')
    >>> comment.message
    'Not raining.'
    >>> comment.word_count
    2
    """
    question = models.ForeignKey('QualitativeQuestion',
                                 on_delete=models.CASCADE)
    language = models.CharField(max_length=3, choices=LANGUAGES)
    message = models.TextField(blank=True)
    flagged = models.BooleanField(default=False)
    tag = models.CharField(max_length=256, blank=True, default='')

    def __unicode__(self):
        return '{0}: "{1}"'.format(self.id, self.message)

    @property
    def word_count(self):
        return len(self.message.split())

    # TODO: add mean rating, number rated, and standard error (i.e., the old
    #       SE field) using the `property decorator`

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
    A `QuantitativeQuestionRating` is a numeric response to a
    `QuantitativeQuestion`.

    Attributes:
        question: A reference to the `QuantitativeQuestion` this rating is in
                  response to.
    """
    question = models.ForeignKey('QuantitativeQuestion',
                                 on_delete=models.CASCADE)

    def __unicode__(self):
        template = 'QuantitativeQuestion {0}: {1}'
        return template.format(self.question_id, self.score)

    class Meta:
        unique_together = ('respondent', 'question')


class CommentRating(Rating):
    """
    A `CommentRating` is a numeric response to a `Comment`.

    Attributes:
        comment: A reference to the `Comment` this comment is in response to.
    """
    comment = models.ForeignKey('Comment', on_delete=models.CASCADE)

    def __unicode__(self):
        return 'Comment {0}: {1}'.format(self.comment_id, self.score)

    class Meta:
        unique_together = ('respondent', 'comment')


class Question(models.Model):
    """
    A `Question` models a prompt presented to the user that requires a
    response.

    Attributes:
        prompt: The prompt in the primary language of the application.
        tag: A short string that summarizes the prompt.
    """
    prompt = models.TextField(blank=True)
    tag = models.CharField(max_length=256, blank=True, default='')

    def __unicode__(self):
        return '{0}: "{1}"'.format(self.id, self.prompt)


class QualitativeQuestion(Question):
    """
    A `QualitativeQuestion` is a `Question` that asks for a comment.

    Attributes:
        comments: A Django `QuerySet` of `Comment`s in response to this
                  question.
    """
    # pylint: disable=model-no-explicit-unicode

    class Meta:
        proxy = True

    @property
    def comments(self):
        return Comment.objects.filter(question=self)


class QuantitativeQuestion(Question):
    """
    A `QuantitativeQuestion` is a `Question` that asks for a numeric rating.

    Attributes:
        mean_score: The mean score given to this `QuantitativeQuestion`.
        num_ratings: The number times respondents have rated this question.
    """
    # pylint: disable=model-no-explicit-unicode

    class Meta:
        proxy = True

    def select_ratings(self, answered=True):
        """
        Select `QuantitativeQuestionRating` instances attached to this
        question.

        Args:
            answered: When `True`, select only `QuantitativeQuestionRating`s
                      where the respondent did not skip this question (whether
                      intentionally or not). When `True`, the scores of the
                      ratings returned are guaranteed to be nonnegative.

        Returns:
            A Django `QuerySet` containing this question's ratings.
        """
        query = QuantitativeQuestionRating.objects.filter(question=self)
        if answered:
            excluded_ratings = [Rating.NOT_RATED, Rating.SKIPPED]
            return query.exclude(score__in=excluded_ratings)
        return query

    @property
    def mean_score(self):
        scores = self.select_ratings().values_list('score', flat=True)
        return sum(scores)/len(scores)

    @property
    def num_ratings(self):
        return self.select_ratings().count()


class Respondent(models.Model):
    """
    A `Respondent` represents a one-time participant in a survey.

    Attributes:
        GENDERS: Choices for the `gender` field. This attribute is a tuple of
                 pairs of strings, of which the second entry is the full gender
                 name and the first is a single-letter abbreviation.
        age: The age of the respondent in years.
        gender: The gender of the respondent, as selected from `GENDERS`.
        location: An open text field that describes the `respondent`'s
                  residence. (In the particular context of the PCARI project,
                  this field should contain the name of the `Respondent`'s
                  barangay.)
        language: The language preferred by this respondent.
        submitted_personal_data: A boolean indicating whether the user
                                 completed the form asking for `age`, `gender`,
                                 and `location`. Because this form is entirely
                                 optional, there is no other way to infer the
                                 `Respondent`'s progression through this stage.
        completed_survey: A boolean indicating whether the user completed the
                          entire survey.
        num_questions_rated: The number of `QuantitativeQuestion`'s answered by
                             this `Respondent`. From this number, we can infer
                             whether this `Respondent` reached the rating stage
                             of the survey.
        num_comments_rated: The number of `Comment`'s reviewed by this
                            `Respondent`. Similarly, we can infer user
                            progression from this attribute.
        comments_made: A Django `QuerySet` of all comments attached to this
                       `Respondent`.
    """
    GENDERS = (
        ('M', 'Male'),
        ('F', 'Female')
    )

    age = models.PositiveSmallIntegerField(default=None, null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDERS, default='',
                              blank=True)
    location = models.CharField(max_length=512, default='', blank=True)
    language = models.CharField(max_length=3, choices=LANGUAGES)
    submitted_personal_data = models.BooleanField(default=False)
    completed_survey = models.BooleanField(default=False)

    def __unicode__(self):
        return '{0}'.format(self.id)

    @property
    def num_questions_rated(self):
        questions = QuantitativeQuestionRating.objects.filter(respondent=self)
        return questions.count()

    @property
    def num_comments_rated(self):
        return CommentRating.objects.filter(respondent=self).count()

    @property
    def comments_made(self):
        return Comment.objects.filter(respondent=self).all()
