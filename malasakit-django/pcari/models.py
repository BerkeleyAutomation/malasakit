from __future__ import unicode_literals

import datetime

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils import timezone


class Translation(models.Model):
    """
    A `Translation` bundles a message with the language it is written in.

    Attributes:
        LANGUAGES: A tuple of pairs (tuples of size two), each of which has a
                   language code as the first entry and the language name as
                   the second. The three-letter language code should be taken
                   from the ISO 639-2 standard.
        phrase: A reference to a model that bundles equivalent translations
                together.
        language: A language code (see the `LANGAUGES` attribute).
        message: The text itself written in `language`.
        word_count: The number of words in the `message` (words are delimited
                    with contiguous whitespace).

    TODO: validate `language` on assignment
    """
    LANGUAGES = (
        ('ENG', 'English'),
        ('FIL', 'Filipino')
    )

    phrase = models.ForeignKey('Phrase', on_delete=models.CASCADE)
    language = models.CharField(max_length=3, choices=LANGUAGES)
    message = models.TextField(null=True, empty=True)

    class Meta:
        unique_together = ('phrase', 'language')

    @property
    def word_count(self):
        return len(self.message.split())


class Phrase(models.Model):
    """
    A `Phrase` groups together equivalent translations.

    Any clients of the `Phrase` class can act language-agnostic.
    """
    tag = models.CharField(max_length=64, null=True, blank=True)

    def get_translation(self, language):
        return self.translation_set.get(language=language).message

    def update_or_create_translation(self, language, message):
        Translation.objects.update_or_create(phrase=self, language=language,
                                             defaults={'message': message})

    def all_translations(self):
        translations = Translation.objects.filter(phrase=self)
        return {translation.language: translation.message
                for translation in translations}


class ResponseMixin(models.Model):
    """
    A `Response` is an abstract model of user-generated data.
    """
    respondent = models.ForeignKey('Respondent', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class Comment(Phrase, ResponseMixin):
    """
    A `Comment` is a textual response to a `QualitativeQuestion`.

    Example usage:

    >>> respondent = Respondent()
    >>> prompt = Phrase(tag='weather-question')
    >>> prompt.update_or_create_translation('ENG', 'How is the weather?')
    >>> question = QualitativeQuestion(prompt=prompt)
    >>> comment = Comment(respondent=respondent, question=question, tag='comment')
    >>> comment.update_or_create_translation('ENG', 'Not raining.')
    """
    question = models.ForeignKey('QualitativeQuestion', on_delete=models.CASCADE)


class Rating(ResponseMixin):
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
    prompt = models.OneToOneField('Phrase', related_name='+', on_delete=models.CASCADE)

    class Meta:
        abstract = True


class QualitativeQuestion(Question):
    @property
    def num_responses(self):
        return Comment.objects.filter(question=self).count()


class QuantitativeQuestion(Question):
    left_end_description = models.OneToOneField('Phrase', related_name='+', on_delete=models.CASCADE)
    right_end_description = models.OneToOneField('Phrase', related_name='+', on_delete=models.CASCADE)

    def select_ratings(self):
        return QuantitativeQuestionRating.objects.filter(question=self)

    @property
    def mean_score(self):
        excluded_ratings = [Rating.NOT_RATED, Rating.SKIPPED]
        scores = list(select_ratings().exclude(score__in=excluded_ratings).all())
        return sum(scores)/len(scores)

    @property
    def num_ratings(self):
        excluded_ratings = [Rating.NOT_RATED, Rating.SKIPPED]
        return select_ratings().exclude(score__in=excluded_ratings).count()


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
