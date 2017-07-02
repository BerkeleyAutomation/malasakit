"""
This module defines unit tests for views.
"""

from __future__ import unicode_literals
import json
import logging
import os
import random
import time
import warnings

from django.conf import settings
from django.db import IntegrityError
from django.test import TestCase, Client
from django.urls import reverse
import numpy as np

from .models import Respondent
from .models import QuantitativeQuestion, QualitativeQuestion
from .models import Comment, QuantitativeQuestionRating, CommentRating
from .views import (generate_ratings_matrix, normalize_ratings_matrix,
                    calculate_principal_components)

PAGE_ENDPOINTS = ['landing', 'quantitative-questions', 'peer-responses',
                  'rate-comments', 'personal-information', 'end']
HTTP_OK = 200

logging.disable(logging.CRITICAL)


def ignore_warnings(function):
    def wrapper(*args, **kwargs):
        warnings.filterwarnings('ignore')
        result = function(*args, **kwargs)
        warnings.resetwarnings()
        return result
    return wrapper


def generate_page_urls(endpoints=PAGE_ENDPOINTS):
    for code, _ in settings.LANGUAGES:
        for endpoint in endpoints:
            yield os.path.join(settings.URL_ROOT, code, endpoint, '')


class ResourceFetchTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_visit_pages(self):
        for url in generate_page_urls():
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            items = dict(response.items())
            self.assertTrue('text/html' in response['Content-Type'].lower())
            self.assertEqual(response.charset.lower(), 'utf-8')

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
    @classmethod
    def setUpTestData(cls):
        question = QuantitativeQuestion(id=1)
        question.save()
        question = QualitativeQuestion(id=1)
        question.save()

    def setUp(self):
        self.client = Client()

    def push(self, responses):
        http_response = self.client.post(reverse('save-response'),
                                         data=json.dumps(responses),
                                         content_type='application/json')
        return http_response

    def test_empty_save(self):
        response = self.push({'respondent-data': {'language': 'en'}})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(QuantitativeQuestionRating.objects.count(), 0)
        self.assertEqual(Comment.objects.count(), 0)
        self.assertEqual(CommentRating.objects.count(), 0)
        self.assertEqual(Respondent.objects.count(), 1)

    def test_valid_data_save(self):
        respondent = Respondent(id=100)
        respondent.save()

        comment = Comment.objects.create(
            respondent=respondent,
            question_id=1,
            message='hello world',
            language='en',
        )

        self.assertEqual(QuantitativeQuestionRating.objects.count(), 0)

        http_response = self.push({
            'question-ratings': {
                '1': 4
            },
            'comments': {
                '1': 'hello world',
            },
            'comment-ratings': {
                str(comment.id): 2
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
        bad_formats = [
            {'question-ratings': [], 'respondent-data': {'language': 'en'}},
            {'question-ratings': 1, 'respondent-data': {'language': 'en'}},
            {'question-ratings': {'?': ''}, 'respondent-data': {'language': 'en'}},
            {'comments': {'?': ''}, 'respondent-data': {'language': 'en'}},
            {'respondent-data': {'age': 140, 'language': 'en'}},
        ]

        for bad_format in bad_formats:
            response = self.push(bad_format)
            self.assertEqual(response.status_code, 400)
            self.assertEqual(QuantitativeQuestionRating.objects.count(), 0)
            self.assertEqual(Comment.objects.count(), 0)
            self.assertEqual(CommentRating.objects.count(), 0)
            self.assertEqual(Respondent.objects.count(), 0)


class PCACorrectnessTestCase(TestCase):
    """ Test the correctness of the principal component analysis. """
    fixtures = ['pca-test-data.yaml']

    def test_ratings_matrix_entries(self):
        results = generate_ratings_matrix()
        respondent_id_map, question_id_map, ratings_matrix = results
        indices = lambda respondent_id, question_id: (respondent_id_map[respondent_id],
                                                      question_id_map[question_id])

        self.assertEqual(ratings_matrix.shape, (3, 2))
        self.assertEqual(ratings_matrix[indices(1, 1)], 9)
        self.assertEqual(ratings_matrix[indices(2, 1)], 0)
        self.assertEqual(ratings_matrix[indices(3, 1)], 1)
        self.assertEqual(ratings_matrix[indices(1, 2)], 6)
        self.assertTrue(np.isnan(ratings_matrix[indices(2, 2)]))
        self.assertTrue(np.isnan(ratings_matrix[indices(3, 2)]))

    @ignore_warnings
    def test_ratings_matrix_normalization(self):
        input_matrices = [
            np.array([[9, 6],
                      [0, np.nan],
                      [1, np.nan]]),
            np.array([[0, 1, 2, np.nan],
                      [np.nan, np.nan, 3, np.nan]]),
        ]
        expected_matrices = [
            np.array([[9 - 10.0/3, 0],
                      [-10.0/3, 0],
                      [1 - 10.0/3, 0]]),
            np.array([[0, 0, -0.5, 0],
                      [0, 0, 0.5, 0]]),
        ]
        for input_matrix, expected in zip(input_matrices, expected_matrices):
            actual = normalize_ratings_matrix(input_matrix)

            self.assertEqual(actual.shape, input_matrix.shape)
            self.assertEqual(expected.shape, input_matrix.shape)
            self.assertEqual(actual.shape, expected.shape)

            error = np.linalg.norm(expected - actual)
            self.assertAlmostEqual(error, 0)

    def test_calculate_principal_components(self):
        normalized_ratings = normalize_ratings_matrix(np.array([[9, 6],
                                                                [0, np.nan],
                                                                [0, np.nan]]))

        actual_components = calculate_principal_components(normalized_ratings, 2)
        expected_components = np.array([[1, 0],
                                        [0, 1]])  # Calculated by hand

        for actual, expected in zip(actual_components, expected_components):
            # The SVD is not unique, so to check that the calculated components
            # are correct, we need only check every pair of components is
            # parallel.
            self.assertEqual(np.linalg.norm(expected), 1)
            self.assertEqual(np.linalg.norm(actual), 1)
            self.assertAlmostEqual(abs(np.dot(actual, expected)), 1)
