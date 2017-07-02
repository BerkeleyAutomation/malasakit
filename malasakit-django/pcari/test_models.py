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
                respondent=Respondent.objects.create(language='en')
            ) for score in [-1, 9, 3, 3, 4, -1]
        ])

        cls.question_no_ratings = QuantitativeQuestion.objects.create()

        cls.comment = Comment.objects.create(
            question=QualitativeQuestion.objects.create(),
            language='en',
            message='Hello world',
            respondent=Respondent.objects.create(language='en'),
        )
        CommentRating.objects.bulk_create([
            CommentRating(
                comment=cls.comment,
                score=score,
                respondent=Respondent.objects.create(language='en')
            ) for score in [-2, 0, 3]
        ])

    def test_num_ratings(self):
        self.assertEqual(self.question.num_ratings, 4)
        QuantitativeQuestionRating.objects.create(
            question=self.question,
            score=6,
            respondent=Respondent.objects.create(language='en')
        )
        self.assertEqual(self.question.num_ratings, 5)
        self.assertEqual(self.question_no_ratings.num_ratings, 0)
        self.assertEqual(self.comment.num_ratings, 2)

    def test_mean_score(self):
        self.assertAlmostEqual(self.question.mean_score, 19.0/4)
        self.assertTrue(math.isnan(self.question_no_ratings.mean_score))
        self.assertAlmostEqual(self.comment.mean_score, 1.5)
        CommentRating.objects.get(score=3).delete()
        self.assertAlmostEqual(self.comment.mean_score, 0)

    def test_mode_score(self):
        self.assertEqual(self.question.mode_score, 3)
        QuantitativeQuestionRating.objects.filter(score=3).update(score=9)
        self.assertEqual(self.question.mode_score, 9)
        self.assertNotEqual(self.comment.mode_score,
                            QuantitativeQuestionRating.NOT_RATED)

    def test_score_stdev(self):
        self.assertAlmostEqual(self.question.score_stdev, 2.87228132327)
        self.assertAlmostEqual(self.comment.score_stdev, 2.1213203435596424)
        CommentRating.objects.get(score=3).delete()
        self.assertTrue(math.isnan(self.comment.score_stdev))

    def test_score_sem(self):
        self.assertAlmostEqual(self.question.score_sem, 1.436140662)
        self.assertTrue(math.isnan(self.question_no_ratings.score_sem))
        self.assertAlmostEqual(self.comment.score_sem, 1.5)


class HistoryTests(TestCase):
    def test_make_copy(self):
        respondent = Respondent.objects.create(age=1, gender='M', location='?')
        copy = respondent.make_copy()
        self.assertEqual(respondent.age, copy.age)
        self.assertEqual(respondent.gender, copy.gender)
        self.assertEqual(respondent.location, copy.location)

    def test_diff(self):
        respondent1 = Respondent.objects.create(age=12, gender='M', location='?')
        respondent2 = Respondent.objects.create(age=12, gender='F', location='?')
        self.assertEqual(set(respondent1.diff(respondent2)), {'id', 'gender'})

        respondent2.gender = 'M'
        respondent2.save()
        self.assertEqual(set(respondent1.diff(respondent2)), {'id'})

    def test_no_grandparent_deletion(self):
        parent = QuantitativeQuestion.objects.create(prompt='Hello world')
        child = QuantitativeQuestion.objects.create(prompt='Hello World',
                                                    predecessor=parent)
        parent.delete()
        child.refresh_from_db()
        self.assertEqual(child.predecessor, None)

    def test_grandparent_deletion(self):
        grandparent = QuantitativeQuestion.objects.create(prompt='hello world')
        parent = QuantitativeQuestion.objects.create(prompt='Hello world',
                                                     predecessor=grandparent)
        child = QuantitativeQuestion.objects.create(prompt='Hello World',
                                                    predecessor=parent)
        parent.delete()
        child.refresh_from_db()
        self.assertEqual(child.predecessor, grandparent)
