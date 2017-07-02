from __future__ import unicode_literals
import math

from django.db import IntegrityError
from django.test import TestCase, TransactionTestCase

from pcari.models import Respondent
from pcari.models import QuantitativeQuestion, QualitativeQuestion
from pcari.models import QuantitativeQuestionRating, Comment, CommentRating


class StatisticsTests(TestCase):
    """ Ensure all descriptive statistics are computed correctly. """
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
    """ Ensure history is tracked correctly. """
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
        parent = QuantitativeQuestion.objects.create(prompt='Hello world',
                                                     active=True)
        child = QuantitativeQuestion.objects.create(prompt='Hello World',
                                                    predecessor=parent,
                                                    active=False)
        parent.delete()
        child.refresh_from_db()
        self.assertEqual(child.predecessor, None)
        self.assertFalse(child.active)

    def test_grandparent_deletion(self):
        grandparent = QuantitativeQuestion.objects.create(prompt='hello world',
                                                          active=False)
        parent = QuantitativeQuestion.objects.create(prompt='Hello world',
                                                     predecessor=grandparent,
                                                     active=True)
        child = QuantitativeQuestion.objects.create(prompt='Hello World',
                                                    predecessor=parent,
                                                    active=False)
        parent.delete()
        child.refresh_from_db()
        self.assertEqual(child.predecessor, grandparent)
        self.assertTrue(grandparent.active)
        self.assertFalse(child.active)

    def test_nonlinear_deletion(self):
        grandparent = QuantitativeQuestion.objects.create(prompt='Hello world')
        parent = QuantitativeQuestion.objects.create(prompt='Hello world.',
                                                     predecessor=grandparent)
        child1 = QuantitativeQuestion.objects.create(prompt='Hello world ...',
                                                     predecessor=parent)
        child2 = QuantitativeQuestion.objects.create(prompt='Hello world?',
                                                     predecessor=parent)
        parent.delete()
        child1.refresh_from_db()
        child2.refresh_from_db()
        self.assertEqual(child1.predecessor, grandparent)
        self.assertEqual(child2.predecessor, grandparent)


class IntegrityTests(TransactionTestCase):
    def test_rating_respondent_unique_together(self):
        respondent = Respondent.objects.create()
        question = QuantitativeQuestion.objects.create()
        rating = QuantitativeQuestionRating.objects.create(
            respondent=respondent,
            question=question,
            score=0,
        )
        with self.assertRaises(IntegrityError):
            QuantitativeQuestionRating.objects.create(respondent=respondent,
                                                      question=question,
                                                      score=1)

        question = QualitativeQuestion.objects.create()
        comment = Comment.objects.create(respondent=Respondent.objects.create(),
                                         question=question)
        rating = CommentRating.objects.create(respondent=respondent,
                                              comment=comment, score=5)
        with self.assertRaises(IntegrityError):
            CommentRating.objects.create(respondent=respondent, comment=comment,
                                         score=5)

        # OK for one respondent to have two comments for the same quantitative
        # question
        Comment.objects.create(respondent=respondent, question=question)
        Comment.objects.create(respondent=respondent, question=question)
