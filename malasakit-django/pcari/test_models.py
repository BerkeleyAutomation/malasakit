from __future__ import unicode_literals

from django.test import TestCase

from .models import Respondent
from .models import QualitativeQuestion
from .models import Comment


class RespondentTests(TestCase):
    pass


class CommentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.question = QualitativeQuestion()
        cls.question.save()

        cls.respondent = Respondent()
        cls.respondent.save()

        cls.english = Comment(question=cls.question, respondent=cls.respondent)
        cls.english.save()

    def test_word_count(self):
        pass
