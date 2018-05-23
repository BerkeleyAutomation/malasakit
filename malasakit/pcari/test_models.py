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
    OptionQuestionChoice,
    Rating,
    Location,
)

RATING_CHOICES = list(range(0, 9)) + [Rating.SKIPPED]


class StatisticsTestCase(TestCase):
    """ Ensure all descriptive statistics are computed correctly. """
    serialized_rollback = True

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
        ])

        cls.question_no_ratings = QuantitativeQuestion.objects.create()

        cls.comment = Comment.objects.create(
            question=QualitativeQuestion.objects.create(),
            language='en',
            message='Hello world',
            respondent=Respondent.objects.create(language='en'),
        )
        CommentRating.objects.bulk_create([
            # Skipped rating should be filtered out
            CommentRating(
                comment=cls.comment,
                score=score,
                respondent=Respondent.objects.create(language='en')
            ) for score in [CommentRating.SKIPPED, 0, 3]
        ] + [
            # TODO: group translated ratings
        ])

        # TODO: fix reload hack
        cls.question = QuantitativeQuestion.objects.filter(pk=cls.question.pk).first()
        cls.question_no_ratings = QuantitativeQuestion.objects.filter(
            pk=cls.question_no_ratings.pk,
        ).first()
        cls.comment = Comment.objects.filter(pk=cls.comment.pk).first()

    def test_num_ratings(self):
        self.assertEqual(self.question.num_ratings, 4)
        QuantitativeQuestionRating.objects.create(
            question=self.question,
            score=6,
            respondent=Respondent.objects.create(language='en')
        )
        self.question = QuantitativeQuestion.objects.filter(
            pk=self.question.pk,
        ).first()
        self.assertEqual(self.question.num_ratings, 5)
        self.assertEqual(self.question_no_ratings.num_ratings, 0)
        self.assertEqual(self.comment.num_ratings, 2)

    def test_mean_score(self):
        self.assertAlmostEqual(self.question.mean_score, 19.0/4)
        self.assertIsNone(self.question_no_ratings.mean_score)
        self.assertAlmostEqual(self.comment.mean_score, 1.5)
        CommentRating.objects.filter(score=3).delete()
        self.comment = Comment.objects.filter(pk=self.comment.pk).first()
        self.assertAlmostEqual(self.comment.mean_score, 0)

    def test_score_stddev(self):
        # Answers are calculated from `np.std` with `ddof=1` (one delta degree of freedom)
        self.assertAlmostEqual(self.question.score_stddev, 2.87228132327)
        self.assertAlmostEqual(self.comment.score_stddev, 2.1213203435596424)
        CommentRating.objects.filter(score=3).delete()
        self.comment = Comment.objects.filter(pk=self.comment.pk).first()
        self.assertIsNone(self.comment.score_stddev)

    def test_score_sem(self):
        # Answers are calculated from `scipy.stats.sem`
        self.assertAlmostEqual(self.question.score_sem, 1.436140662)
        self.assertIsNone(self.question_no_ratings.score_sem)
        self.assertAlmostEqual(self.comment.score_sem, 1.5)


class PropertyTestCase(TestCase):
    """ Test other dynamically computed model attributes. """
    serialized_rollback = True

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
        num_filtered = num_questions_presented - num_questions_rated
        scores = [
            random.randrange(10) for _ in range(num_questions_rated)
        ] + [QuantitativeQuestionRating.SKIPPED]*num_filtered

        random.shuffle(scores)
        for score in scores:
            QuantitativeQuestionRating.objects.create(
                question=QuantitativeQuestion.objects.create(),
                respondent=respondent,
                score=score,
            )

        self.assertEqual(respondent.num_questions_rated, num_questions_rated,
                         'Failed with:' + ', '.join(map(unicode, scores)))
        QuantitativeQuestionRating.objects.all().delete()
        self.assertEqual(respondent.num_questions_rated, 0)

    def test_num_comments_rated(self):
        respondent = Respondent.objects.create()
        question = QualitativeQuestion.objects.create()
        num_comments_presented = random.randrange(100)
        num_comments_rated = random.randint(0, num_comments_presented)
        num_filtered = num_comments_presented - num_comments_rated
        scores = [
            random.randrange(10) for _ in range(num_comments_rated)
        ] + [QuantitativeQuestionRating.SKIPPED]*num_filtered

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
                         'Failed with:' + ', '.join(map(unicode, scores)))
        CommentRating.objects.all().delete()
        self.assertEqual(respondent.num_comments_rated, 0)

    def test_auto_add_timestamp_order(self):
        question = QuantitativeQuestion.objects.create()
        questions = [
            QuantitativeQuestionRating.objects.create(
                question=question,
                respondent=Respondent.objects.create(),
                score=random.choice(RATING_CHOICES),
            ) for _ in range(random.randrange(100))
        ]
        for first, second in zip(questions[:-1], questions[1:]):
            self.assertLess(first.timestamp, second.timestamp)


class IntegrityTestCase(TransactionTestCase):
    """ Ensure the data passes tests for uniqueness and not being null. """
    serialized_rollback = True

    def test_rating_respondent_unique_together(self):
        respondent = Respondent.objects.create()
        question = QuantitativeQuestion.objects.create()
        rating = QuantitativeQuestionRating.objects.create(
            respondent=respondent,
            question=question,
            score=random.choice(RATING_CHOICES),
        )
        with self.assertRaises(IntegrityError):
            QuantitativeQuestionRating.objects.create(respondent=respondent,
                                                      question=question,
                                                      score=random.choice(RATING_CHOICES))

        question = QualitativeQuestion.objects.create()
        comment = Comment.objects.create(respondent=Respondent.objects.create(),
                                         question=question)
        rating = CommentRating.objects.create(respondent=respondent,
                                              comment=comment, score=random.choice(RATING_CHOICES))
        with self.assertRaises(IntegrityError):
            CommentRating.objects.create(respondent=respondent, comment=comment,
                                         score=random.choice(RATING_CHOICES))

        # OK for one respondent to have two comments for the same quantitative
        # question
        Comment.objects.create(respondent=respondent, question=question)
        Comment.objects.create(respondent=respondent, question=question)


class ValidationTestCase(TestCase):
    """ Ensure validation catches invalid input while allowing valid input. """
    serialized_rollback = True

    def test_quantitative_question_rating_bound_validation(self):
        unbounded_question = QuantitativeQuestion.objects.create(
            min_score=None,
            max_score=None
        )
        for _ in range(random.randrange(100)):
            QuantitativeQuestionRating(respondent=Respondent.objects.create(),
                                       score=random.randint(0, 10000),
                                       question=unbounded_question).full_clean()

        bounded_question = QuantitativeQuestion.objects.create(
            min_score=5,
            max_score=20,
        )
        sentinels = [QuantitativeQuestionRating.SKIPPED]*10
        for score in [random.randint(5, 20) for _ in range(10)] + sentinels:
            QuantitativeQuestionRating(respondent=Respondent.objects.create(),
                                       question=bounded_question,
                                       score=score).full_clean()

        scores = [random.randint(21, 10000) for _ in range(10)]
        scores += [random.randrange(0, 5) for _ in range(10)]
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
