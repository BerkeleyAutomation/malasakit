"""
This module defines unit tests.
"""

from __future__ import unicode_literals
import json
import os
import random
import time

from django.conf import settings
from django.db import IntegrityError
from django.test import TestCase, Client
from django.urls import reverse

from .models import Respondent
from .models import QuantitativeQuestion, QualitativeQuestion
from .models import Comment, QuantitativeQuestionRating, CommentRating

PAGE_ENDPOINTS = ['landing', 'quantitative-questions', 'peer-responses',
                  'rate-comments', 'personal-information', 'end']
API_RETRIEVAL_ENDPOINTS = ['fetch-comments', 'fetch-qualitative-questions']


def generate_page_urls(endpoints=PAGE_ENDPOINTS):
    for code, _ in settings.LANGUAGES:
        for endpoint in endpoints:
            yield os.path.join(settings.URL_ROOT, code, endpoint)


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


class ResourceFetchTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        # TODO: mock up qualitative question instances

    def test_fetch_qualitative_questions(self):
        response = self.client.get(reverse('fetch-qualitative-questions'))
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(data, dict))

        for key in data:
            question_id = int(key)
            translated_prompts = data[key]
            self.assertTrue(isinstance(translated_prompts, dict))
            question = QualitativeQuestion.objects.get(id=question_id)

    def test_fetch_comments(self):
        pass


class ResponseSaveTestCase(TestCase):
    fixtures = ['questions.yaml']

    def setUp(self):
        self.client = Client()

    def push(self, responses):
        http_response = self.client.post(reverse('save-response'),
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


class PageMarkupTestCase(TestCase):
    """ This test inspects all HTML served to the client. """
    def setUp(self):
        self.client = Client()

    def test_html_validity(self):
        pass


class PerformanceTestCase(TestCase):
    """ Test the runtime of public-facing endpoints. """
    ITERATIONS = 100
    ACCEPTABLE_SPEED_THRESHOLD = 0.95
    ACCEPTABLE_SPEED_TIMEOUT = 0.5  # seconds

    def setUp(self):
        self.client = Client()

    def percentage_acceptable(self, runtimes):
        return sum(runtime < self.ACCEPTABLE_SPEED_TIMEOUT
                   for runtime in runtimes)/len(runtimes)

    def test_page_runtimes(self):
        runtimes = {}
        for _ in range(self.ITERATIONS):
            for url in generate_page_urls():
                if url not in runtimes:
                    runtimes[url] = []

                start = time.time()
                response = self.client.get(url)
                end = time.time()

                time_elapsed = end - start
                runtimes[url].append(time_elapsed)

        for url in generate_page_urls():
            self.assertGreater(self.percentage_acceptable(runtimes[url]),
                               self.ACCEPTABLE_SPEED_THRESHOLD)
