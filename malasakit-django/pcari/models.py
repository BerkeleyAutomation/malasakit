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


class TemplatingText(Text):
    """
    `TemplatingText` is developer-generated text used for instructions and questions.
    """


class Question(models.Model):
    prompt = models.OneToOne('TemplatingText', on_delete=models.CASCADE)

    class Meta:
        abstract = True

    @property
    def num_responses(self):
        return self.objects.filter(question=)


class QualitativeQuestion(models.Model):
    prompt = models.ForeignKey('Templating', on_delete=models.CASCADE)


class QuantitativeQuestion(models.Model):
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


class Comment(models.Model):
    question = models.ForeignKey('QualitativeQuestion', on_delete=models.CASCADE)
    author = models.ForeignKey('Respondent', on_delete=models.CASCADE)
    
    text = models.OneToOneField('Text', on_delete=models.CASCADE)


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


class Tag(models.Model):
    name = models.CharField(max_length=32)

    def get_text(self, language):
        translation = Translation.objects.get(tag=self, language=language)
        return translation.text


class Translation(models.Model):
    tag = models.ForeignKey('Tag', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('tag', 'language')


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


class QuantitativeQuestion(models.Model):
    qid = models.AutoField(primary_key=True)
    question = models.CharField(max_length=500, default="")
    average_score = models.FloatField(default = 0)
    number_rated = models.IntegerField(default = 0)
    tag = models.CharField(max_length=50, default="")
    filipino_tag = models.CharField(max_length=50, default="")
    filipino_question = models.CharField(max_length=500, default="walang filipino pagsasalin")
    def get_question(self,language=None):
        # print "what comes into get Q " + language 
        if language == "English":
            q = self.question
        else:
            # print "in model filipno"
            q = self.filipino_question
        return {'qid':self.qid,'question':q}


class QualitativeQuestion(models.Model):
    qid = models.AutoField(primary_key=True)
    question = models.CharField(max_length=500, default="")
    filipino_question = models.CharField(max_length=500, default="walang filipino pagsasalin")


# If a user does not rate a question, the score will be -2.
# If they choose to skip a question, the score will be -1.
# For qualitative questions, the score will remain -2.
class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index = True)
    qid = models.IntegerField(default = -1)
    date = models.DateTimeField(auto_now_add=True)
    score = models.IntegerField(default = -2)
    response = models.CharField(max_length = 1000, default = "")
    accounted = models.BooleanField(default=False)

    class Meta:
        unique_together = (('user', 'qid'),)


class Comment(models.Model):
    LANGUAGE_CHOICES = (
    ('English', 'English'),
    ('Filipino', 'Filipino'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index = True)
    comment = models.CharField(max_length = 1000, default = "", null = True, blank=True)
    filipino_comment = models.CharField(max_length = 1000, default = "", null = True, blank=True)
    date = models.DateTimeField(auto_now_add = True)
    average_score = models.FloatField(default = 0)
    number_rated = models.IntegerField(default = 0)
    tag = models.CharField(max_length=200, default = "", null=True)
    original_language = models.CharField(max_length=15, choices=LANGUAGE_CHOICES, null=True, blank=True)
    se = models.FloatField(default = 0, null = True, blank = True);


class CommentRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index = True)
    cid = models.IntegerField(default = -1)
    score = models.IntegerField(default = 0)
    date = models.DateTimeField(auto_now_add = True)
    accounted = models.BooleanField(default=False)


class UserProgression(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,)
    date = models.DateTimeField(auto_now_add = True)
    landing = models.BooleanField(default=False)
    rating = models.BooleanField(default=False)
    num_rated = models.IntegerField(default=0)
    review = models.BooleanField(default=False)
    bloom = models.BooleanField(default=False)
    peer_rating = models.BooleanField(default=False)
    num_peer_rated = models.IntegerField(default=0)
    personal_data = models.NullBooleanField(default=False, null=True)
    comment = models.BooleanField(default=False)
    logout = models.BooleanField(default=False)
    completion_rate = models.IntegerField(default = 0)


class Progression(models.Model):
    landing = models.FloatField(default=0)
    rating = models.FloatField(default=0)
    review = models.FloatField(default=0)
    bloom = models.FloatField(default=0)
    peer_rating = models.FloatField(default=0)
    comment = models.FloatField(default=0)
    logout = models.FloatField(default=0)


class FlaggedComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index = True)
    comment = models.CharField(max_length = 1000, default = "", null = True)
    filipino_comment = models.CharField(max_length = 1000, default = "", null = True)
    date = models.DateTimeField(auto_now_add = False)
    average_score = models.FloatField(default = 0)
    number_rated = models.IntegerField(default = 0)
    tag = models.CharField(max_length=200, default = "", null=True)
