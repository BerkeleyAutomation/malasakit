from __future__ import unicode_literals
import json
import random

from django.db import IntegrityError
from django.test import TestCase, Client
from django.urls import reverse

from .models import Respondent
from .models import QuantitativeQuestion, QualitativeQuestion
from .models import Comment, QuantitativeQuestionRating, CommentRating


class UserFeedbackTestCase(TestCase):
    fixtures = ['questions.yaml', 'user-generated.yaml']

    def setUp(self):
        self.quant_question = QuantitativeQuestion.objects.first()
        self.qual_question = QualitativeQuestion.objects.first()

    def test_quantitative_question_statistics(self):
        self.assertEqual(self.quant_question.num_ratings, 3)
        self.assertAlmostEqual(self.quant_question.mean_score, 4.0/3)

    def test_quantitative_question_rating_uniqueness(self):
        prev_respondents = [rating.respondent for rating in
                            QuantitativeQuestionRating.objects.all()]
        prev_respondent = random.sample(prev_respondents, 1)[0]
        with self.assertRaises(IntegrityError):
            QuantitativeQuestionRating(respondent=prev_respondent,
                                       score_history_text='2',
                                       question=self.quant_question).save()

    def test_quantitative_question_rating_timestamp_order(self):
        timestamps = [rating.timestamp for rating in
                      QuantitativeQuestionRating.objects.all()]
        for first, second in zip(timestamps[:-1], timestamps[1:]):
            self.assertLessEqual(first, second)

    def test_comment_retrieval(self):
        comments = self.qual_question.comments
        self.assertEqual(comments.count(), 2)
        messages = [comment.message for comment in comments.all()]
        self.assertEqual(messages, ['bob', 'race car'])

    def test_comment_word_count(self):
        self.assertEqual(Comment.objects.get(id=1).word_count, 1)
        self.assertEqual(Comment.objects.get(id=2).word_count, 2)


class ResponseSaveTestCase(TestCase):
    fixtures = ['questions.yaml']

    def setUp(self):
        self.client = Client()

    def push(self, responses):
        http_response = self.client.post(reverse('pcari:save-response'),
                                         data=json.dumps(responses),
                                         content_type='application/json')
        return http_response

    def test_empty_save(self):
        self.push({'respondent-data': {'language': 'en'}})
        self.assertEqual(QuantitativeQuestionRating.objects.count(), 0)
        self.assertEqual(Comment.objects.count(), 0)
        self.assertEqual(CommentRating.objects.count(), 0)
        self.assertEqual(Respondent.objects.count(), 1)

    def test_valid_data_save(self):
        respondent = Respondent(id=100)
        respondent.save()

        comment = Comment(respondent=respondent, question_id=1,
                          message='hello world', language='en')
        comment.save()

        self.assertEqual(QuantitativeQuestionRating.objects.count(), 0)

        http_response = self.push({
            'question-ratings': {
                '1': [4]
            },
            'comments': {
                '1': 'hello world',
            },
            'comment-ratings': {
                str(comment.id): [2]
            },
            'respondent-data': {
                'language': 'tl'
            }
        })

        self.assertEqual(http_response.status_code, 200)
        self.assertEqual(QuantitativeQuestionRating.objects.count(), 1)
        self.assertEqual(Comment.objects.count(), 2)
        self.assertEqual(CommentRating.objects.count(), 1)
        self.assertEqual(Respondent.objects.count(), 2)

        self.assertEqual(Comment.objects.last().message, 'hello world')

    def test_invalid_data_save(self):
        http_response = self.push({
            # Bad format
            'question-ratings': [
                {}
            ]
        })

        self.assertEqual(http_response.status_code, 400)
        self.assertEqual(QuantitativeQuestionRating.objects.count(), 0)
        self.assertEqual(Respondent.objects.count(), 0)
