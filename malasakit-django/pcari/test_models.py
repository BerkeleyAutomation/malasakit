from __future__ import unicode_literals
import math

from django.test import TestCase

from pcari.models import Respondent
from pcari.models import QuantitativeQuestion, QualitativeQuestion
from pcari.models import QuantitativeQuestionRating, Comment, CommentRating


class StatisticsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.question = QuantitativeQuestion.objects.create()
        QuantitativeQuestionRating.objects.bulk_create([
            QuantitativeQuestionRating(
                question=cls.question,
                score=score,
                respondent=Respondent.objects.create()
            ) for score in [-1, 9, 3, 4]
        ])

        cls.question_no_ratings = QuantitativeQuestion.objects.create()

        cls.comment = Comment.objects.create(
            question=QualitativeQuestion.objects.create(),
            language='en',
            message='Hello world',
            respondent=Respondent.objects.create(),
        )
        CommentRating.objects.bulk_create([
            CommentRating(
                comment=cls.comment,
                score=score,
                respondent=Respondent.objects.create()
            ) for score in [-2, 0, 3]
        ])

    def test_num_ratings(self):
        self.assertEqual(self.question.num_ratings, 3)
        QuantitativeQuestionRating.objects.create(
            question=self.question,
            score=6,
            respondent=Respondent.objects.create()
        )
        self.assertEqual(self.question.num_ratings, 4)
        self.assertEqual(self.question_no_ratings.num_ratings, 0)
        self.assertEqual(self.comment.num_ratings, 2)

    def test_mean_score(self):
        self.assertAlmostEqual(self.question.mean_score, 16.0/3)
        self.assertTrue(math.isnan(self.question_no_ratings.mean_score))
        self.assertAlmostEqual(self.comment.mean_score, 1.5)
        CommentRating.objects.get(score=3).delete()
        self.assertAlmostEqual(self.comment.mean_score, 0)
