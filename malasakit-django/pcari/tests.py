from __future__ import unicode_literals
import random

from django.db import IntegrityError
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
