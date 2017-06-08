from __future__ import unicode_literals
import random

from django.db import IntegrityError
from django.test import Client
from django.test import TestCase

from .models import Respondent
from .models import QuantitativeQuestion, QualitativeQuestion
from .models import Comment, QuantitativeQuestionRating, CommentRating


class UserFeedbackTestCase(TestCase):
    def setUp(self):
        self.quant_question = QuantitativeQuestion(
            prompt='What number am I thinking of?',
            tag='test-quant-question'
        )
        self.qual_question = QualitativeQuestion(
            prompt='List a palindrome.',
            tag='test-qual-question'
        )

        self.quant_question.save()
        self.qual_question.save()

        quant_question_scores = [3, 0, 1, QuantitativeQuestionRating.NOT_RATED,
                                 QuantitativeQuestionRating.SKIPPED]
        for score in quant_question_scores:
            respondent = Respondent()
            respondent.save()
            QuantitativeQuestionRating(respondent=respondent, score=score,
                                       question=self.quant_question).save()

        for key, comment in enumerate(['bob', 'race car']):
            respondent = Respondent()
            respondent.save()
            Comment(id=key, respondent=respondent, question=self.qual_question,
                    language='ENG', message=comment).save()

    def test_quantitative_question_statistics(self):
        self.assertEqual(self.quant_question.num_ratings, 3)
        self.assertAlmostEqual(self.quant_question.mean_score, 4.0/3)

    def test_quantitative_question_rating_uniqueness(self):
        prev_respondents = [rating.respondent for rating in
                            QuantitativeQuestionRating.objects.all()]
        prev_respondent = random.sample(prev_respondents, 1)[0]
        with self.assertRaises(IntegrityError):
            QuantitativeQuestionRating(respondent=prev_respondent, score=2,
                                       question=self.quant_question).save()

    def test_quantitative_question_rating_timestamp_order(self):
        timestamps = [rating.timestamp for rating in
                      QuantitativeQuestionRating.objects.all()]
        for first, second in zip(timestamps[:-1], timestamps[1:]):
            self.assertLess(first, second)

    def test_comment_retrieval(self):
        comments = self.qual_question.comments
        self.assertEqual(comments.count(), 2)
        messages = [comment.message for comment in comments.all()]
        self.assertEqual(messages, ['bob', 'race car'])

    def test_comment_word_count(self):
        self.assertEqual(Comment.objects.get(id=0).word_count, 1)
        self.assertEqual(Comment.objects.get(id=1).word_count, 2)


class ViewTestCase(TestCase):
    """Test case for methods in views.py.

    Simple sanity checks for some of the methods for now while I'm refactoring.
    If we decide we want to keep it then we can add more tests later.
    """
    def setUp(self):
        """Setup- throw in some dummy questions
        TODO: Per Jon's reccomendation, figure out how to keep the dummy db for
        all tests (address if tests take painfully long)
        """
        self.client = Client()
        self.quant_question = QuantitativeQuestion(
            prompt='What number am I thinking of?',
            tag='test-quant-question'
        )
        self.qual_question = QualitativeQuestion(
            prompt='List a palindrome.',
            tag='test-qual-question'
        )

        self.quant_question.save()
        self.qual_question.save()

    def test_get_question_ids(self):
        """Expecting a dict with key 'qids', value is a list of numbers. In this
        case the list should be length 1.
        """
        response = self.client.get('/pcari/get-question-ids/')
        self.assertEqual(len(response.json()['qids']), 1)

    def test_get_question(self):
        """Expecting a dict with keys 'qid' and 'question', values are an int
        and the text of the question respectively"""
        response = self.client.get('/pcari/get-question/1/')
        question = QuantitativeQuestion.objects.get(id=1)
        self.assertEqual(response.json()['qid'], question.id)
        self.assertEqual(response.json()['question'], question.prompt)

    def test_get_question_no_exist(self):
        """Expecting a 404 error because the question does not exist!"""
        response = self.client.get('/pcari/get-question/2/')
        self.assertEqual(response.status_code, 404)
