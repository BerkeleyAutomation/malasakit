from __future__ import unicode_literals

import datetime

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils import timezone
from django.contrib.auth.models import User


class Tag(models.Model):
    name = models.CharField(max_length=32)

    def get_text(self, language):
        translation = Translation.objects.get(tag=self, language=language)
        return translation.text


class Translation(models.Model):
    # Use ISO 639-2 for the first entry (save space usage)
    LANGUAGES = (
        ('ENG', 'English'),
        ('FIL', 'Filipino')
    )

    tag = models.ForeignKey('Tag', on_delete=models.CASCADE)
    language = models.CharField(max_length=3, choices=LANGUAGES)
    text = models.TextField()

    class Meta:
        unique_together = ('tag', 'language')


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

class UserData(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,)
    age = models.IntegerField(default=0, null = True, blank=True)
    barangay = models.CharField(max_length=500, default="", null = True, blank=True)
    GENDER_CHOICES = (
    ('M', 'Male'),
    ('F', 'Female'),
    )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null = True, blank=True)
    LANGUAGE_CHOICES = (
    ('English', 'English'),
    ('Filipino', 'Filipino'),
    )
    language = models.CharField(max_length=15, choices=LANGUAGE_CHOICES, default="Filipino")

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
