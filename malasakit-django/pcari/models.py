"""
Model definitions.

This module defines how information used by Malasakit is structured and how the
Python layer interfaces with a database.

Attributes:
    LANGUAGES: A tuple of languages. Each language is represented as a tuple of
        two elements: a code and a translated full name. For instance, the
        language code for "English" would be "en". This attribute is pulled
        from the project `settings` lazily.
    MODELS: A dictionary mapping model names to models. This attribute
        essentially acts as a lookup table by name, and is useful for
        determining whether a model with a given name exists.
"""

from __future__ import unicode_literals
from collections import Counter
import json

from django.conf import settings
from django.db import models

__all__ = ['Comment', 'QuantitativeQuestionRating', 'CommentRating', 'QualitativeQuestion',
'QuantitativeQuestion', 'Respondent', 'OptionQuestion', 'OptionQuestionChoice', 'MODELS']

LANGUAGES = settings.LANGUAGES


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
    A `StatisticsMixin` adds descriptive statistics capabilities to a model
    that accepts ratings.

    To use this mixin on a model, have the model inherit from this class after
    it inherits from some subclass of `django.db.models.Model`. The model must
    have a related name `ratings` (that is, the reverse relationship of a
    many-to-one) that accesses a `QuerySet` of instances of a `Rating`-derived
    model.
    """
    @property
    def scores(self):
        """ Access a list of scores. """
        active_ratings = self.ratings.filter(active=True)
        return active_ratings.values_list('scores', flat=True)

    @property
    def num_ratings(self):
        """ Return the number of ratings for this instance. """
        return len(self.scores)

    @property
    def mean_score(self):
        """ Calculate the mean score. """
        scores = self.scores
        if len(scores):
            return float(sum(scores))/len(scores)
        return float('nan')

    @property
    def mode_score(self):
        """ Calculate the mode score. """
        most_common = Counter(self.scores).most_common(1)
        return most_common[0][0] if most_common else float('nan')

    @property
    def score_stdev(self):
        """ Calculate the standard deviation of the scores. """
        scores = self.scores
        if len(scores) < 2:
            return float('nan')
        mean_score = float(sum(scores))/len(scores)
        squared_residuals = (pow(score - mean_score, 2) for score in scores)
        return (sum(squared_residuals)/(len(scores) - 1))**0.5

    @property
    def score_std_error(self):
        """ Calculate the standard error of the mean of the scores. """
        num_ratings = self.num_ratings
        if num_ratings > 1:
            return self.score_stdev/num_ratings**0.5
        return float('nan')


class History(models.Model):
    """
    The `History` abstract model records how one model instance derives from
    another.

    The database should be insert-only such that when updating a field of a
    model instance, a new instance is created, rather than overwriting the
    attribute of an old instance. This model effectively does the bookkeeping
    necessary so that we can see which instances are active and how they have
    changed over time.

    Attributes:
        predecessor: A reference to the instance this instance is based on. If
            this instance is the first of its kind (e.g., a new question), this
            reference should be `None` (which is the default value).
        active: Whether this instance is considered usable or not. Typically,
            when a new model instance is created from an old one when updating
            a field, the old one is marked as inactive.
    """
    predecessor = models.ForeignKey('self', on_delete=models.SET_NULL,
                                    null=True, default=None,
                                    related_name='successors')
    active = models.BooleanField(default=True)

    def make_copy(self):
        """
        Make a copy of the current model, excluding unique fields.

        Returns:
            An unsaved copy of `self`.
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

        Returns:
            A generator of field names where the two instances differ.
        """
        model = self.__class__
        assert isinstance(other, model)
        for field in get_direct_fields(model):
            if getattr(self, field.name) != getattr(other, field.name):
                yield field.name

    @property
    def predecessors(self):
        """
        Yields a sequence of predecessors, from the most recent to the original.

        Returns:
            A generator of model instances.
        """
        current = self
        while current.predecessor is not None:
            current = current.predecessor
            yield current

    class Meta:
        abstract = True


class Response(History):
    """
    A `Response` is an abstract model of respondent-generated data.

    Attributes:
        respondent: A reference to the response author.
        timestamp: The date and time at which this response was made. (By
            default, this field is automatically set to the time when the
            instance is created. This field is not editable.)
    """
    respondent = models.ForeignKey('Respondent', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class Rating(Response):
    """
    A `Rating` is an abstract model of a numeric response.

    Attributes:
        NOT_RATED: A sentinel value assigned to a `Rating` that the respondent
            never submitted (that is, a default value).
        SKIPPED: A sentinel value assigned to a `Rating` where the user
            intentionally chose to decline rating a question or a comment.
        score: An integer that quantifies a rating. (No scale is provided, by
            design. Interpreting the `score` is not the responsibility of this
            model.)
    """
    NOT_RATED = -2
    SKIPPED = -1

    score = models.SmallIntegerField(default=NOT_RATED)

    class Meta:
        abstract = True


class QuantitativeQuestionRating(Rating):
    """
    A `QuantitativeQuestionRating` rates a `QuantitativeQuestion`. A respondent
    can only rate a quantitative question once.

    Attributes:
        question: The quantitative question rated.
    """
    question = models.ForeignKey('QuantitativeQuestion',
                                 on_delete=models.CASCADE,
                                 related_name='ratings')

    def __unicode__(self):
        template = 'Rating {0} to {1}'
        return template.format(self.score, self.question)

    class Meta:
        unique_together = ('respondent', 'question')


class CommentRating(Rating):
    """
    A `CommentRating` rates a `Comment`. A respondent can only rate a comment
    once.

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
    A `Comment` is an open-ended text response to a `QualitativeQuestion`.

    Attributes:
        question: The `QualitativeQuestion` this comment answers.
        language: A language code.
        message: The comment's contents itself written in `language`.
        flagged: A boolean indicating whether this comment was flagged for
            further inspection. A flagged comment will not show up to other
            respondents.
        tag: A short string that summarizes this comment's message.
        word_count: The number of words in the `message`. (Words are delimited
            with contiguous whitespace.)
    """
    MAX_COMMENT_DISPLAY_LEN = 140

    question = models.ForeignKey('QualitativeQuestion',
                                 on_delete=models.CASCADE,
                                 related_name='comments')
    language = models.CharField(max_length=8, choices=LANGUAGES)
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
    A `Question` models all prompts presented to a respondent.

    Attributes:
        prompt: The prompt in English. (Translations can be specified with
            Django's localization system.)
        tag: A short string in English that summarizes the prompt.
    """
    prompt = models.TextField(blank=True, default='')
    tag = models.CharField(max_length=256, blank=True, default='')

    class Meta:
        abstract = True


class QualitativeQuestion(Question):
    """
    A `QualitativeQuestion` is a `Question` that asks for a comment.

    Attributes:
        input_type: What interface to use for collecting qualitative question
            responses.
    """
    input_type = 'textarea'

    def __unicode__(self):
        return 'Qualitative question {0}: "{1}"'.format(self.id, self.prompt)


class QuantitativeQuestion(Question, StatisticsMixin):
    """
    A `QuantitativeQuestion` is a `Question` that asks for a numeric rating.

    Attributes:
        INPUT_TYPE_CHOICES: A tuple of input type choices, each of which is a
            two-element tuple consisting of the shorthand and the name of an
            input type. Current options are:
                range: Render the question as a "slider".
                number: Render the question as a number-only text field.
        left_anchor: The text that describes the minimum score. For a range
            input type, this text is rendered on the left end of the slider.
        right_anchor: The text that describes the maximum score. For a range
            innput type, this text is rendered on the right end of the slider.
        min_score: The smallest possible score for this question. A value of
            `None` is treated as negative infinity (that is, no lower bound).
        max_score: The largest possible score for this question. A value of
            `None` is treated as positive infinity (that is, no upper bound).
        input_type: A string specifying how the input should be rendered.
    """
    INPUT_TYPE_CHOICES = (
        ('range', 'Range'),
        ('number', 'Number'),
    )

    left_anchor = models.TextField(blank=True, default='')
    right_anchor = models.TextField(blank=True, default='')
    min_score = models.SmallIntegerField(default=0, null=True)
    max_score = models.SmallIntegerField(default=9, null=True)
    input_type = models.CharField(max_length=16, choices=INPUT_TYPE_CHOICES,
                                  default='range')

    def __unicode__(self):
        return 'Quantitative question {0}: "{1}"'.format(self.id, self.prompt)


class OptionQuestion(Question):
    """
    An `OptionQuestion` is a `Question` that asks the respondent to select one
    element from a set of unordered choices.

    Attributes:
        INPUT_TYPE_CHOICES: A tuple of input type choices, each of which is a
            two-element tuple consisting of the shorthand and the name of an
            input type. Current options are:
                select: Render the question as a dropdown menu.
                radio: Render the question as a list of radio buttons.
        _options_text: A string representing a list of options in JSON.
        options: A wrapper around `_options_text` that automatically serializes
            and unserializes a Python list of options. This is the preferred
            way of manipulating the list of options.
        input_type: A string specifying how the input should be rendered.
    """
    INPUT_TYPE_CHOICES = (
        ('select', 'Select'),
        ('radio', 'Radio'),
    )

    _options_text = models.TextField(blank=True, default=json.dumps([]))
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


class OptionQuestionChoice(Response):
    """
    An `OptionQuestionChoice` is a response to an `OptionQuestion`.

    Attributes:
        question: The `OptionQuestion` answered.
        option: The option selected by the respondent. This must be an element
            of `question.options`.
    """
    question = models.ForeignKey('OptionQuestion', on_delete=models.CASCADE,
                                 related_name='selections')
    option = models.TextField(blank=True)

    def __unicode__(self):
        template = 'Option question choice {0}: "{1}"'
        return template.format(self.question_id, self.option)

    class Meta:
        unique_together = ('respondent', 'question')


class Respondent(History):
    """
    A `Respondent` represents a one-time participant in a survey.

    Attributes:
        GENDERS: Choices for the `gender` field. This attribute is a tuple of
            pairs of strings, of which the second entry is the full gender name
            and the first is a single-letter abbreviation.
        age: The age of the respondent in years.
        gender: The gender of the respondent, as selected from `GENDERS`.
        location: An open text field that describes the respondent's residence.
            (In the particular context of the Philippines, this field should
            contain the respondent's province, city or municipality, and
            barangay.)
        language: The language preferred by this respondent.
        submitted_personal_data: A boolean indicating whether the user
            completed the form asking for `age`, `gender`, and `location`.
            Because this form is entirely optional, there is no other way to
            infer the `Respondent`'s progression through this stage.
        completed_survey: A boolean indicating whether the user completed the
            entire survey.
        num_questions_rated: The number of `QuantitativeQuestion`'s answered by
            this `Respondent`. From this number, we can infer whether this
            `Respondent` reached the rating stage of the survey.
        num_comments_rated: The number of `Comment`'s reviewed by this
            `Respondent`. Similarly, we can infer user progression from this
            attribute.
        comments: A Django `QuerySet` of all comments attached to this
            respondent.
    """
    GENDERS = (
        ('M', 'Male'),
        ('F', 'Female'),
    )

    age = models.PositiveSmallIntegerField(default=None, null=True)
    gender = models.CharField(max_length=1, choices=GENDERS, blank=True,
                              default='')
    location = models.CharField(max_length=512, blank=True, default='')
    language = models.CharField(max_length=8, choices=LANGUAGES)
    submitted_personal_data = models.BooleanField(default=False)
    completed_survey = models.BooleanField(default=False)

    def __unicode__(self):
        return 'Respondent {0}'.format(self.id)

    def num_questions_rated(self):
        ratings = QuantitativeQuestionRating.objects.filter(respondent=self)
        ratings = ratings.exclude(rating__in=[Rating.NOT_RATED, Rating.SKIPPED])
        return ratings.count()

    num_questions_rated.short_description = 'Number of questions rated'
    num_questions_rated = property(num_questions_rated)

    def num_comments_rated(self):
        ratings = CommentRating.objects.filter(respondent=self)
        ratings = ratings.exclude(rating__in=[Rating.NOT_RATED, Rating.SKIPPED])
        return ratings.count()

    num_comments_rated.short_description = 'Number of comments rated'
    num_comments_rated = property(num_comments_rated)

    @property
    def comments(self):
        return Comment.objects.filter(respondent=self).all()


MODELS = {
    model.__name__: model for model in [
        Comment, QuantitativeQuestionRating, CommentRating, QualitativeQuestion,
        QuantitativeQuestion, Respondent, OptionQuestion, OptionQuestionChoice
    ]
}
