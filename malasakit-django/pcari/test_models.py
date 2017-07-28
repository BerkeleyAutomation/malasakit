"""
This module defines unit tests of model behavior.
"""

from __future__ import unicode_literals
import math
import random

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase, TransactionTestCase

from pcari.models import (
    Respondent,
    QuantitativeQuestion,
    QualitativeQuestion,
    OptionQuestion,
    QuantitativeQuestionRating,
    Comment,
    CommentRating,
    OptionQuestionChoice
)


class StatisticsTests(TestCase):
    """ Ensure all descriptive statistics are computed correctly. """
    @classmethod
    def setUpTestData(cls):
        cls.question = QuantitativeQuestion.objects.create()
        QuantitativeQuestionRating.objects.bulk_create([
            # Skipped ratings should be filtered out
            QuantitativeQuestionRating(
                question=cls.question,
                score=score,
                respondent=Respondent.objects.create(language='en')
            ) for score in [QuantitativeQuestionRating.SKIPPED, 9, 3, 3, 4,
                            QuantitativeQuestionRating.SKIPPED]
        ] + [
            # A bunch of inactive ratings that should be filtered out
            QuantitativeQuestionRating(
                question=cls.question,
                score=random.randint(-2, 9),
                respondent=Respondent.objects.create(language='en'),
                active=False
            ) for _ in range(random.randrange(100))
        ])

        cls.question_no_ratings = QuantitativeQuestion.objects.create()

        cls.comment = Comment.objects.create(
            question=QualitativeQuestion.objects.create(),
            language='en',
            message='Hello world',
            respondent=Respondent.objects.create(language='en'),
        )
        CommentRating.objects.bulk_create([
            # `-2` (not rated) should be filtered out
            CommentRating(
                comment=cls.comment,
                score=score,
                respondent=Respondent.objects.create(language='en')
            ) for score in [-2, 0, 3]
        ] + [
            # A bunch of inactive ratings that should be filtered out
            CommentRating(
                comment=cls.comment,
                score=random.randint(-2, 9),
                respondent=Respondent.objects.create(language='en'),
                active=False
            ) for _ in range(random.randrange(100))
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
        CommentRating.objects.filter(score=3, active=True).delete()
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
        CommentRating.objects.filter(score=3, active=True).delete()
        self.assertTrue(math.isnan(self.comment.score_stdev))

    def test_score_sem(self):
        self.assertAlmostEqual(self.question.score_sem, 1.436140662)
        self.assertTrue(math.isnan(self.question_no_ratings.score_sem))
        self.assertAlmostEqual(self.comment.score_sem, 1.5)


class PropertyTests(TestCase):
    """ Test other dynamically computed model attributes. """
    def test_option_question_choice_wrapping(self):
        question = OptionQuestion.objects.create(
            _options_text='["red", "green", "blue"]',
        )
        self.assertEqual(question.options, ['red', 'green', 'blue'])
        question.options = ['orange']
        question.save()
        self.assertEqual(question._options_text, '["orange"]')

    def test_comment_word_count(self):
        question = QualitativeQuestion.objects.create()
        respondent = Respondent.objects.create()
        comment = Comment.objects.create(message='Word count is four.',
                                         respondent=respondent,
                                         question=question)
        self.assertEqual(comment.word_count, 4)
        comment.message = ''
        self.assertEqual(comment.word_count, 0)

    def test_num_questions_rated(self):
        respondent = Respondent.objects.create()
        num_questions_presented = random.randrange(100)
        num_questions_rated = random.randint(0, num_questions_presented)
        scores = [
            random.randrange(10) for _ in range(num_questions_rated)
        ] + [
            # A bunch of scores that should be filtered out
            random.choice([QuantitativeQuestionRating.NOT_RATED,
                           QuantitativeQuestionRating.SKIPPED])
            for _ in range(num_questions_presented - num_questions_rated)
        ]

        random.shuffle(scores)
        for score in scores:
            QuantitativeQuestionRating.objects.create(
                question=QuantitativeQuestion.objects.create(),
                respondent=respondent,
                score=score,
            )

        self.assertEqual(respondent.num_questions_rated, num_questions_rated,
                         'Failed with:' + ', '.join(map(str, scores)))
        QuantitativeQuestionRating.objects.all().delete()
        self.assertEqual(respondent.num_questions_rated, 0)

    def test_num_comments_rated(self):
        respondent = Respondent.objects.create()
        question = QualitativeQuestion.objects.create()
        num_comments_presented = random.randrange(100)
        num_comments_rated = random.randint(0, num_comments_presented)
        scores = [
            random.randrange(10) for _ in range(num_comments_rated)
        ] + [
            # A bunch of scores that should be filtered out
            random.choice([QuantitativeQuestionRating.NOT_RATED,
                           QuantitativeQuestionRating.SKIPPED])
            for _ in range(num_comments_presented - num_comments_rated)
        ]

        random.shuffle(scores)
        for score in scores:
            comment = Comment.objects.create(
                respondent=Respondent.objects.create(),
                question=question,
            )
            CommentRating.objects.create(
                respondent=respondent,
                comment=comment,
                score=score
            )

        self.assertEqual(respondent.num_comments_rated, num_comments_rated,
                         'Failed with:' + ', '.join(map(str, scores)))
        CommentRating.objects.all().delete()
        self.assertEqual(respondent.num_comments_rated, 0)

    def test_auto_add_timestamp_order(self):
        question = QuantitativeQuestion.objects.create()
        questions = [
            QuantitativeQuestionRating.objects.create(
                question=question,
                respondent=Respondent.objects.create(),
                score=random.randint(-2, 9)
            ) for _ in range(random.randrange(100))
        ]
        for first, second in zip(questions[:-1], questions[1:]):
            self.assertLess(first.timestamp, second.timestamp)


class HistoryTests(TestCase):
    """ Ensure history is tracked correctly. """
    def test_make_copy(self):
        respondent = Respondent.objects.create(age=1, gender='M', location='?')
        copy = respondent.make_copy()
        copy.save()
        self.assertNotEqual(respondent, copy)
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

    def test_simple_parent_deletion(self):
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

    def test_predecessors(self):
        chain_length = random.randrange(1, 100)
        current = None
        primary_keys = []
        for _ in range(chain_length):
            current = QualitativeQuestion.objects.create(predecessor=current)
            primary_keys.append(current.pk)

        self.assertEqual(current.pk, primary_keys.pop())
        for predecessor in current.predecessors:
            self.assertEqual(predecessor.pk, primary_keys.pop())
        self.assertEqual(primary_keys, [])


class IntegrityTests(TransactionTestCase):
    """ Ensure the data passes tests for uniqueness and not being null. """
    def test_rating_respondent_unique_together(self):
        respondent = Respondent.objects.create()
        question = QuantitativeQuestion.objects.create()
        rating = QuantitativeQuestionRating.objects.create(
            respondent=respondent,
            question=question,
            score=random.randint(-2, 9),
        )
        with self.assertRaises(IntegrityError):
            QuantitativeQuestionRating.objects.create(respondent=respondent,
                                                      question=question,
                                                      score=random.randint(-2, 9))

        question = QualitativeQuestion.objects.create()
        comment = Comment.objects.create(respondent=Respondent.objects.create(),
                                         question=question)
        rating = CommentRating.objects.create(respondent=respondent,
                                              comment=comment, score=random.randint(-2, 9))
        with self.assertRaises(IntegrityError):
            CommentRating.objects.create(respondent=respondent, comment=comment,
                                         score=random.randint(-2, 9))

        # OK for one respondent to have two comments for the same quantitative
        # question
        Comment.objects.create(respondent=respondent, question=question)
        Comment.objects.create(respondent=respondent, question=question)


class ValidationTests(TestCase):
    """ Ensure validation catches invalid input while allowing valid input. """
    def test_quantitative_question_rating_bound_validation(self):
        unbounded_question = QuantitativeQuestion.objects.create(
            min_score=None,
            max_score=None
        )
        for _ in range(random.randrange(100)):
            QuantitativeQuestionRating(respondent=Respondent.objects.create(),
                                       score=random.randint(-10000, 10000),
                                       question=unbounded_question).full_clean()

        bounded_question = QuantitativeQuestion.objects.create(
            min_score=0,
            max_score=20,
        )

        sentinels = [QuantitativeQuestionRating.SKIPPED,
                     QuantitativeQuestionRating.NOT_RATED]
        for score in [random.randint(0, 20) for _ in range(10)] + sentinels:
            QuantitativeQuestionRating(respondent=Respondent.objects.create(),
                                       question=bounded_question,
                                       score=score).full_clean()

        scores = [random.randint(21, 10000) for _ in range(10)]
        scores += [random.randint(-10000, -3) for _ in range(10)]
        for score in scores:
            with self.assertRaises(ValidationError):
                QuantitativeQuestionRating(respondent=Respondent.objects.create(),
                                           question=bounded_question,
                                           score=score).full_clean()

    def test_option_question_choice_validation(self):
        question = OptionQuestion()
        question.options = ['a', 'b', 'c']
        question.save()

        for option in question.options:
            OptionQuestionChoice(respondent=Respondent.objects.create(),
                                 question=question, option=option).full_clean()

        for option in ['A', '?', '--', 'd']:
            with self.assertRaises(ValidationError):
                OptionQuestionChoice(respondent=Respondent.objects.create(),
                                     question=question, option=option).full_clean()

    def test_respondent_age_validation(self):
        for age in [0, 10, 60, 110, 120]:
            Respondent(age=age).full_clean()

        for age in [-1, 121, 65535]:
            with self.assertRaises(ValidationError) as context:
                Respondent(age=age).full_clean()
            errors = dict(context.exception)
            self.assertEqual(len(errors), 1)
            self.assertTrue('age' in errors)

    def test_respondent_gender_validation(self):
        for gender in ['', 'M', 'F']:
            Respondent(gender=gender).full_clean()

        for gender in ['m', 'f', '?', 'Male', '**']:
            with self.assertRaises(ValidationError) as context:
                Respondent(gender=gender).full_clean()
            errors = dict(context.exception)
            self.assertEqual(len(errors), 1)
            self.assertTrue('gender' in errors)
