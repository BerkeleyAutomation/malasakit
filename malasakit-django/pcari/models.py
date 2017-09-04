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

__all__ = ['Comment', 'QuantitativeQuestionRating', 'CommentRating',
           'QualitativeQuestion', 'QuantitativeQuestion', 'Respondent',
           'OptionQuestion', 'OptionQuestionChoice']

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


class StatisticsMixin:
    """
    A ``StatisticsMixin`` adds descriptive statistics capabilities to a model
    that accepts ratings.

    To use this mixin on a model, have the model inherit from this class after
    it inherits from :class:`django.db.models.Model` (or some subclass of
    ``Model``). The model must have a related name ``ratings`` (that is, the
    reverse relationship of a many-to-one) that accesses a ``QuerySet`` of
    instances of a model that inherits from :class:`Rating`.

    All properties exclude skipped ratings (see :attr:`Rating.SKIPPED`).

    Attributes:
        scores: A flat ``QuerySet`` of integer scores.
        num_ratings (int): The number of ratings the object has received.
        mean_score (float): The mean score the object has received, or
            ``float('nan')`` if the object has no ratings.
        mode_score (float): The most common score this object received, or
            ``float('nan')`` if the object has no ratings.
        score_stdev (float): The corrected standard deviation of this object's
            scores, or ``float('nan')`` if the object has fewer than two
            ratings.
        score_sem (float): The standard error of the mean of this object's
            scores, or ``float('nan')`` if the object has fewer than two
            ratings.
    """
    @property
    def scores(self):
        active_ratings = self.ratings.filter(active=True)
        active_ratings = active_ratings.exclude(
            score=Rating.SKIPPED
        )
        return active_ratings.values_list('score', flat=True)

    def num_ratings(self):
        return self.scores.count()
    num_ratings.short_description = 'Number of ratings'
    num_ratings = property(num_ratings)

    @property
    def mean_score(self):
        mean = self.scores.aggregate(Avg('score'))['score__avg']
        return mean if mean is not None else float('nan')

    @property
    def mode_score(self):
        aggregation = self.scores.annotate(count=Count('score'))
        most_common = aggregation.order_by('-count').first()
        return most_common if most_common is not None else float('nan')

    @property
    def _score_aggregates(self):
        query = self.scores.annotate(score_squared=F('score')*F('score'))
        values = query.aggregate(
            Sum('score'), Sum('score_squared'), Count('score')
        )
        return values['score__sum'], values['score_squared__sum'], values['score__count']

    @property
    def score_stdev(self):
        score_sum, score_squared_sum, num_scores = self._score_aggregates
        if num_scores < 2:
            return float('nan')
        stdev2 = (score_squared_sum - pow(score_sum, 2)/num_scores)/(num_scores - 1)
        return pow(stdev2, 0.5)

    @property
    def score_sem(self):
        score_sum, score_squared_sum, num_scores = self._score_aggregates
        if num_scores < 2:
            return float('nan')
        stdev2 = (score_squared_sum - pow(score_sum, 2)/num_scores)/(num_scores - 1)
        return pow(stdev2, 0.5)/num_scores**0.5


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
    """
    respondent = models.ForeignKey('Respondent', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class Rating(Response):
    """
    A ``Rating`` is an abstract model of a numeric response.

    Attributes:
        SKIPPED: A sentinel value assigned to a ``Rating`` where the user
            intentionally chose to decline rating a question or a comment.
        score: An integer that quantifies a rating. (No scale is provided, by
            design. Interpreting the :attr:`score` is not the responsibility of
            this model.)
    """
    SKIPPED = None

    score = models.PositiveIntegerField(default=SKIPPED, null=True, blank=True)

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

        if not (min_score <= self.score <= max_score) and self.score != Rating.SKIPPED:
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
    A ``Comment`` is an open-ended text response to a
    :class:`QualitativeQuestion`.

    Attributes:
        MAX_COMMENT_DISPLAY_LEN (int): The maximum number of characters in the
            :attr:`message` to display in this comment's string representation.
        question: The question this comment answers.
        language (str): A language code.
        message (str): The comment's contents itself written in `language`.
        flagged (bool): Whether this comment was flagged for further
            inspection. A flagged comment will not show up to other
            respondents.
        tag (str): A short summary of this comment's message.
        word_count (int): The number of words in the `message`. (Words are
            delimited with contiguous whitespace.)
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

    @property
    def word_count(self):
        return len(self.message.split())


class Question(History):
    """
    A ``Question`` models all prompts presented to a respondent.

    Attributes:
        prompt (str): The prompt in English. (Translations can be specified
            with Django's localization system.)
        tag (str): A short string in English that summarizes the prompt.
        order (int): A key used for sorting questions in ascending order before
            being displayed. This value need not be unique--ties are broken
            arbitrarily. Questions without an ``order`` are displayed last.
    """
    prompt = models.TextField(blank=True, default='')
    tag = models.CharField(max_length=256, blank=True, default='')
    order = models.IntegerField(null=True, blank=True, default=None,
                                help_text='Questions are displayed using this '
                                          'value sorted in ascending order. '
                                          'Questions without a given <tt>order</tt> '
                                          'are displayed last.')

    class Meta:
        abstract = True


class QualitativeQuestion(Question):
    """
    A ``QualitativeQuestion`` is a question that asks for a :class:`Comment`.

    Attributes:
        input_type (str): What interface to use for collecting qualitative
            question responses.
    """
    input_type = 'textarea'

    def __unicode__(self):
        return 'Qualitative question {0}: "{1}"'.format(self.id, self.prompt)


class QuantitativeQuestion(Question, StatisticsMixin):
    """
    A ``QuantitativeQuestion`` is a question that asks for a numeric rating.

    Attributes:
        INPUT_TYPE_CHOICES (tuple): Input type choices, each of which is a
            two-element tuple consisting of the shorthand and the name of an
            input type. Current options are:
            * `range`: Render the question as a "slider".
            * `number`: Render the question as a number-only text field.
        left_anchor (str): The text that describes the minimum score. For a
            range :attr:`input_type`, this text is rendered on the left end of
            the slider.
        right_anchor (str): The text that describes the maximum score. For a
            range :attr:`input_type`, this text is rendered on the right end
            of the slider.
        min_score (int): The smallest possible score for this question. A value
            of `None` is treated as negative infinity (that is, no lower bound).
        max_score (int): The largest possible score for this question. A value
            of `None` is treated as positive infinity (that is, no upper bound).
        input_type (str): How the input should be rendered.
    """
    INPUT_TYPE_CHOICES = (
        ('range', 'Range'),
        ('number', 'Number'),
    )

    left_anchor = models.TextField(blank=True, default='')
    right_anchor = models.TextField(blank=True, default='')
    min_score = models.PositiveSmallIntegerField(default=0, null=True)
    max_score = models.PositiveSmallIntegerField(default=9, null=True)
    input_type = models.CharField(max_length=16, choices=INPUT_TYPE_CHOICES,
                                  default='range')

    def __unicode__(self):
        return 'Quantitative question {0}: "{1}"'.format(self.id, self.prompt)


class OptionQuestion(Question):
    """
    An ``OptionQuestion`` is a question that asks the respondent to select one
    element from a set of unordered choices.

    Attributes:
        INPUT_TYPE_CHOICES (tuple): Input type choices, each of which is a
            two-element tuple consisting of the shorthand and the name of an
            input type. Current options are:
            * `select`: Render the question as a dropdown menu.
            * `radio`: Render the question as a list of radio buttons.
        _options_text (str): A JSON list of options. This field should only be
            used internally by this model.
        options (list of str): A wrapper around :attr:`_options_text` that
            automatically serializes and unserializes a Python list of options.
            This is the preferred way of manipulating the list of options.
        input_type (str): How the input should be rendered.
    """
    INPUT_TYPE_CHOICES = (
        ('select', 'Select'),
        ('radio', 'Radio'),
    )

    _options_text = models.TextField(
        blank=True,
        default=json.dumps([]),
        verbose_name='Options as JSON',
        help_text='A JSON list has the form: <tt>["Choice A", "Choice B"]</tt>. '
                  'Each option is wrapped in double quotation marks. '
                  'The options are then separated by commas within the square brackets.',
    )
    input_type = models.CharField(max_length=16, choices=INPUT_TYPE_CHOICES,
                                  default='select')

    @property
    def options(self):
        return json.loads(self._options_text)

    @options.setter
    def options(self, options_list):
        self._options_text = json.dumps(list(options_list))

    def __unicode__(self):
        return 'Option question {0}: "{1}"'.format(self.id, self.prompt)

    def clean_fields(self, exclude=None):
        super(OptionQuestion, self).clean_fields(exclude=exclude)
        exclude = exclude or []
        if '_options_text' not in exclude:
            try:
                options = json.loads(self._options_text)
                assert isinstance(options, list)
                for option in options:
                    assert isinstance(option, (str, unicode))
            except (ValueError, AssertionError):
                raise ValidationError(_('"_options_text" is not a JSON list of strings'))

            if not len(options):
                raise ValidationError(_('"_options_text" must contain at least one option'))


class OptionQuestionChoice(Response):
    """
    An ``OptionQuestionChoice`` is a response to an :class:`OptionQuestion`.

    Attributes:
        question: The question answered.
        option (str): The option selected by the respondent. This must be an
            element of ``question.options``.
    """
    question = models.ForeignKey('OptionQuestion', on_delete=models.CASCADE,
                                 related_name='selections')
    option = models.TextField(blank=True)

    def clean(self):
        """
        Validates the value of :attr:`option`.

        Raises:
            ValidationError: if :attr:`option` is not an element of
                ``question.options``.
        """
        super(OptionQuestionChoice, self).clean()
        if self.option and self.option not in self.question.options:
            raise ValidationError(_('"%(option)s" is not a valid option'),
                                  code='invalid-selection',
                                  params={'option': str(self.option)})

    def __unicode__(self):
        template = 'Option question choice {0}: "{1}"'
        return template.format(self.question_id, self.option)

    class Meta:
        unique_together = ('respondent', 'question')


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
        ('', '(Empty)'),
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
    uuid = models.UUIDField(unique=True, default=None, editable=False,
                            null=True, blank=True)

    def __unicode__(self):
        return 'Respondent {0}'.format(self.id)

    def num_questions_rated(self):
        ratings = QuantitativeQuestionRating.objects.filter(respondent=self)
        return ratings.exclude(score=Rating.SKIPPED).count()
    num_questions_rated.short_description = 'Number of questions rated'
    num_questions_rated = property(num_questions_rated)

    def num_comments_rated(self):
        ratings = CommentRating.objects.filter(respondent=self)
        return ratings.exclude(score=Rating.SKIPPED).count()
    num_comments_rated.short_description = 'Number of comments rated'
    num_comments_rated = property(num_comments_rated)

    @property
    def comments(self):
        return Comment.objects.filter(respondent=self).all()
