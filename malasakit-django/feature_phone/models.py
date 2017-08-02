"""
Model definitions.

This module defines how information used by Malasakit is structured and how the
Python layer interfaces with a database.

The core of the database consists of concrete models derived from the abstract
:class:`Question` and :class:`Response` models. Generally speaking, there is a
one-to-one correspondence between a type of question and its associated
response.

References:
    * `Django Model Reference <https://docs.djangoproject.com/en/dev/topics/db/models/>`_
    * `Django Field Reference <https://docs.djangoproject.com/en/dev/ref/models/fields/>`_
    * `QuerySet API <https://docs.djangoproject.com/en/dev/ref/models/querysets/>`_
    * `The contenttypes framework <https://docs.djangoproject.com/en/dev/ref/contrib/contenttypes/>`_

Attributes:
    LANGUAGES (tuple): Available languages. Each language is represented as a
        tuple of two elements: a code and a translated full name. For instance,
        the language code for "English" would be "en". This attribute is pulled
        from the project ``settings`` lazily.
"""

from __future__ import division, unicode_literals
import json

from django.core.exceptions import ValidationError
from django.conf import settings
from django.core.validators import RegexValidator
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import F, Count, Avg, Sum
from django.utils.translation import ugettext_lazy as _

# Create your models here.

__all__ = ['Comment', 'QuantitativeQuestionRating', 'CommentRating',
           'QualitativeQuestion', 'QuantitativeQuestion', 'Respondent']

LANGUAGES = settings.LANGUAGES
_LANGUAGE_CODES = [''] + [code for code, name in LANGUAGES]
LANGUAGE_VALIDATOR = RegexValidator(r'^({0})$'.format('|'.join(_LANGUAGE_CODES)))


def get_concrete_fields(model):
    return [field for field in model._meta.get_fields()
            if not field.is_relation
                or field.one_to_one
                or (field.many_to_one and field.related_model)]


def get_direct_fields(model):
    return [field for field in model._meta.get_fields()
            if not field.auto_created or field.concrete]


class History(models.Model):
    """
    The ``History`` abstract model records how one model instance derives from
    another.

    The database should be insert-only such that when updating a field of a
    model instance, a new instance is created, rather than overwriting the
    attribute of an old instance. This model effectively implements a primitive
    form of version control to determine which instances are active and how
    instances have been edited.

    Attributes:
        predecessor: A reference to the instance this instance is based on. If
            this instance is the first of its kind (e.g., a new question), this
            reference should be `None` (which is the default value). This
            allows for a tree structure of revisions, where the ``predecessor``
            points to a "parent node" (analogous to ``git`` without merging).
            A sequence of predecessors should never be cyclical.
        active (bool): A flag indicating whether this instance is considered
            usable or not. Typically, when a new model instance is created from
            an old one when updating a field, the old instance is marked as
            inactive.
        predecessors: A generator of predecessors, from the most recent to the
            original. Analogous to crawling up the revision tree.
    """
    predecessor = models.ForeignKey('self', on_delete=models.SET_NULL,
                                    null=True, blank=True, default=None,
                                    related_name='successors')
    active = models.BooleanField(default=True)

    def make_copy(self):
        """
        Make a copy of the current model, excluding unique fields.

        Returns:
            An unsaved copy of ``self``.
        """
        model = self.__class__
        copy = model()
        for field in get_direct_fields(model):
            if field.editable and not field.unique:
                value = getattr(self, field.name)
                setattr(copy, field.name, value)

        return copy

    def diff(self, other):
        """
        Find fields where the two instances have different values.

        Args:
            other: An instance of the same model.

        Yields:
            str: A field name where the two instances have different values.

        Raises:
            AssertionError: if ``self`` and ``other`` are not instances of the
                same model.
        """
        model = self.__class__
        assert isinstance(other, model)
        for field in get_direct_fields(model):
            if getattr(self, field.name) != getattr(other, field.name):
                yield field.name

    @property
    def predecessors(self):
        current = self
        while current.predecessor is not None:
            current = current.predecessor
            yield current

    class Meta:
        abstract = True



class Response(History):
    """
    A ``Response`` is an abstract model of respondent-generated data.

    Attributes:
        respondent: A reference to the response author.
        timestamp (datetime.datetime): When this response was made. (By
            default, this field is automatically set to the time when the
            instance is created. This field is not editable.)
        audio: A FilePathField pointing to the audio recording of the rating.
    """
    respondent = models.ForeignKey('Respondent', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    file_path = models.FilePathField(path=MEDIA_ROOT)
    # path to audio files in the media directory

    class Meta:
        abstract = True

class Rating(Response):
    """
    A ``Rating`` is an abstract model of a numeric response.

    Attributes:
        NOT_RATED: A sentinel value assigned to a ``Rating`` that the
            respondent never submitted (that is, a default value).
        SKIPPED: A sentinel value assigned to a ``Rating`` where the user
            intentionally chose to decline rating a question or a comment.
        score: An integer that quantifies a rating. (No scale is provided, by
            design. Interpreting the :attr:`score` is not the responsibility of
            this model.)
    """
    NOT_RATED = -2
    SKIPPED = -1

    score = models.SmallIntegerField(default=NOT_RATED)

    class Meta:
        abstract = True


class QuantitativeQuestionRating(Rating):
    """
    A ``QuantitativeQuestionRating`` rates a :class:`QuantitativeQuestion`. A
    respondent can only rate a quantitative question once.

    Attributes:
        question: The quantitative question rated.
    """
    question = models.ForeignKey('QuantitativeQuestion',
                                 on_delete=models.CASCADE,
                                 related_name='ratings')

    def clean(self):
        """
        Validates the :attr:`score` falls between ``question.min_score`` and
        ``question.max_score``.

        Raises:
            ValidationError: if the score is not legal.
        """
        super(QuantitativeQuestionRating, self).clean()
        min_score = self.question.min_score
        if min_score is None:
            min_score = float('-inf')
        max_score = self.question.max_score
        if max_score is None:
            max_score = float('inf')

        sentinels = [Rating.SKIPPED, Rating.NOT_RATED]
        if not (min_score <= self.score <= max_score) and self.score not in sentinels:
            raise ValidationError(_('Score not in min and max bounds'),
                                  code='score-out-of-bounds')

    def __unicode__(self):
        template = 'Rating {0} to {1}'
        return template.format(self.score, self.question)

    class Meta:
        unique_together = ('respondent', 'question')


class CommentRating(Rating):
    """
    A ``CommentRating`` rates a :class:`Comment`. A respondent can only rate a
    comment once.

    Attributes:
        comment: The comment rated.
    """
    comment = models.ForeignKey('Comment', on_delete=models.CASCADE,
                                related_name='ratings')

    def __unicode__(self):
        return 'Rating {0} to {1}'.format(self.score, self.comment)

    class Meta:
        unique_together = ('respondent', 'comment')


class Comment(Response, StatisticsMixin):
    """
    A ``Comment`` is an open-ended audio response to a
    :class:`QualitativeQuestion`.

    Attributes:
        MAX_COMMENT_DISPLAY_LEN (int): The maximum number of characters in the
            :attr:`message` to display in this comment's string representation.
        question: The question this comment answers.
        language (str): A language code. Language of comment assigned
            based on the language the user chooses?
        message (str): The transcribed contents of the message
        flagged (bool): Whether this comment was flagged for further
            inspection. A flagged comment will not show up to other
            respondents.
        tag (str): A short summary of this comment's message.
    """
    MAX_COMMENT_DISPLAY_LEN = 140

    question = models.ForeignKey('QualitativeQuestion',
                                 on_delete=models.CASCADE,
                                 related_name='comments')
    language = models.CharField(max_length=8, choices=LANGUAGES, blank=True,
                                default='', validators=[LANGUAGE_VALIDATOR])
    message = models.TextField(blank=True, default='')
    flagged = models.BooleanField(default=False)
    tag = models.CharField(max_length=256, blank=True, default='')

    def __unicode__(self):
        if self.message is not None and self.message.strip():
            message = self.message
            if len(message) > self.MAX_COMMENT_DISPLAY_LEN:
                message = message[:self.MAX_COMMENT_DISPLAY_LEN] + ' ...'
            return 'Comment {1}: "{0}"'.format(message, self.id)
        return '-- Empty response --'



class Question(History):
    """
    A ``Question`` models all prompts presented to a respondent in a particular
    language.

    Attributes:
        language (str): A language code. Refers to the language of the audio
            file associated with this question.
        file_path: Path to the audio file for this question.
        question_text: The associated text version of this question. ForeignKey
            to a pcari.Question model.
        tag (str): A short string in English that summarizes the prompt.
        response_time (int): number of seconds allotted to a response
    """
    language = models.CharField(max_length=8, choices=LANGUAGES, blank=True,
                                default='', validators=[LANGUAGE_VALIDATOR])
    file_path = models.FilePathField(path=MEDIA_ROOT)
    tag = models.CharField(max_length=256, blank=True, default='')
    response_time = models.PositiveSmallIntegerField(default=5,null=True)

    class Meta:
        abstract = True


class QualitativeQuestion(Question):
    """
    A ``QualitativeQuestion`` is a question that asks for a :class:`Comment`.

    Attributes:
        response_time (int): number of seconds allotted to a response
    """
    response_time = models.PositiveSmallIntegerField(default=15,null=True)
    # do we want to override Question.response_time?


class QuantitativeQuestion(Question, StatisticsMixin):
    """
    A ``QuantitativeQuestion`` is a question that asks for a numeric rating.

    Attributes:
        min_score (int): The smallest possible score for this question. A value
            of `None` is treated as negative infinity (that is, no lower bound).
        max_score (int): The largest possible score for this question. A value
            of `None` is treated as positive infinity (that is, no upper bound).
        response_time (int): number of seconds allotted to a response
    """
    min_score = 0 # fixed bc of PH team digit recognition limitations
    max_score = 9
    response_time = models.PositiveSmallIntegerField(default=5,null=True)


class Respondent(History):
    """
    A ``Respondent`` represents a one-time participant in a survey.

    Attributes:
        GENDERS (tuple): Choices for the :attr:`gender` field. Each gender is a
            pair of strings, of which the second entry is the gender's full
            name and the first is a single-letter abbreviation.
        age (int): The age of the respondent in years.
        gender (str): The gender of the respondent, as selected from
            :attr:`GENDERS` (an abbreviation).
        location (str): An open text field that describes the respondent's
            residence. (In the particular context of the Philippines, this
            field should contain the respondent's province, city or
            municipality, and barangay.)
        language (str): The language preferred by this respondent. Selected
            from :attr:`pcari.models.LANGUAGES`.
        submitted_personal_data (bool): Whether the user completed the form
            asking for :attr:`age`, :attr:`gender`, and :attr:`location`.
            Because this form is entirely optional, there is no other way to
            infer a respondent's progression through this stage.
        completed_survey (bool): Whether the respondent completed the entire
            survey.
        num_questions_rated (int): The number of quantitative questions
            answered by this respondent. From this number, one can infer whether
            this respondent reached the rating stage of the survey. This
            excludes questions the respondent skipped or otherwise did not rate.
        num_comments_rated (int): The number of comments reviewed by this
            respondent. Similarly, one can infer user progression from this
            attribute. This excludes comments the respondent did not rate.
        comments: A Django ``QuerySet`` of all comments attached to this
            respondent.
    """
    GENDERS = (
        ('M', 'Male'),
        ('F', 'Female'),
    )

    age = models.PositiveSmallIntegerField(default=None, null=True, blank=True,
                                           validators=[MinValueValidator(0),
                                                       MaxValueValidator(120)])
    gender = models.CharField(max_length=1, choices=GENDERS, blank=True,
                              default='', validators=[RegexValidator(r'^(|M|F)$')])
    location = models.CharField(max_length=512, blank=True, default='')
    language = models.CharField(max_length=8, choices=LANGUAGES, blank=True,
                                default='', validators=[LANGUAGE_VALIDATOR])
    submitted_personal_data = models.BooleanField(default=False)
    completed_survey = models.BooleanField(default=False)

    def __unicode__(self):
        return 'Respondent {0}'.format(self.id)

    def num_questions_rated(self):
        ratings = QuantitativeQuestionRating.objects.filter(respondent=self)
        ratings = ratings.exclude(score=Rating.NOT_RATED).exclude(score=Rating.SKIPPED)
        return ratings.count()
    num_questions_rated.short_description = 'Number of questions rated'
    num_questions_rated = property(num_questions_rated)

    def num_comments_rated(self):
        ratings = CommentRating.objects.filter(respondent=self)
        ratings = ratings.exclude(score=Rating.NOT_RATED).exclude(score=Rating.SKIPPED)
        return ratings.count()
    num_comments_rated.short_description = 'Number of comments rated'
    num_comments_rated = property(num_comments_rated)

    @property
    def comments(self):
        return Comment.objects.filter(respondent=self).all()
