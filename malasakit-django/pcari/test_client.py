import datetime
import logging
import os
import re
import time
import types

from django.test import tag, TestCase
from django.test.testcases import LiveServerThread, QuietWSGIRequestHandler
from django.core.servers.basehttp import WSGIServer
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.shortcuts import reverse
from selenium.webdriver import Chrome, ChromeOptions, Firefox
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchAttributeException

from pcari.models import QuantitativeQuestionRating, Comment, CommentRating
from pcari.models import QuantitativeQuestion, QualitativeQuestion
from pcari.models import Respondent

logging.disable(logging.CRITICAL)


def get_attribute_safe(self, name, default=None):
    try:
        return self.get_attribute(name)
    except NoSuchAttributeException:
        return default
WebElement.get_attribute_safe = get_attribute_safe


def set_range_value(self, value):
    if not (self.tag_name == 'input' and self.get_attribute_safe('type') == 'range'):
        raise ValueError('not a range element')
    min_value = int(self.get_attribute_safe('min', 0))
    max_value = int(self.get_attribute_safe('max', 100))
    if not (min_value <= value <= max_value):
        raise ValueError('value {0} does not fall between {1} and {2} for range'.format(
            value, min_value, max_value
        ))

    current = int(self.get_attribute('value'))
    difference = value - current
    direction = Keys.RIGHT if difference > 0 else Keys.LEFT
    for _ in range(abs(difference)):
        self.send_keys(direction)
WebElement.set_range_value = set_range_value


def use_drivers(*test_drivers):
    def make_subtest(name, test_driver_cls, test_method):
        def subtest(self):
            driver = test_driver_cls()
            test_method(self, driver)
        subtest.__name__ = name
        return subtest

    def wrap_test_suite(test_suite):
        for test_name in dir(test_suite):
            if test_name.startswith('test'):
                obj = getattr(test_suite, test_name)
                if isinstance(obj, types.MethodType):
                    for index, test_driver_cls in enumerate(test_drivers):
                        subtest_name = obj.__name__ + '_' + str(index)
                        subtest = make_subtest(subtest_name, test_driver_cls, obj)
                        setattr(test_suite, subtest_name, subtest)
                    delattr(test_suite, test_name)
        return test_suite
    return wrap_test_suite


def make_test_web_driver(driver_base, **options):
    class TestWebDriver(driver_base):
        def __init__(self):
            super(TestWebDriver, self).__init__(**options)

        def start(self):
            self.implicitly_wait(10)

        def stop(self):
            self.quit()

        @property
        def local_storage(self):
            try:
                self.execute_script('return localStorage;');
            except WebDriverException:
                raise TypeError('`localStorage` API is unsupported')
            return self.execute_script("""
                var items = {};
                for (var index = 0; index < localStorage.length; index++) {
                    var key = localStorage.key(index);
                    items[key] = JSON.parse(localStorage.getItem(key));
                }
                return items;
            """)

        def spoof_time_change(self, time_change):
            delta = int(1000*time_change.total_seconds())
            self.execute_script("""
            if (!('_getTime' in Date.prototype)) {{
                Date.prototype._getTime = Date.prototype.getTime;
            }}
            Date.prototype.getTime = function() {{
                return {delta} + this._getTime();
            }}
            """.format(delta=delta))
    return TestWebDriver


_CHROME_OPTIONS = ChromeOptions()
_CHROME_OPTIONS.add_argument('headless')
_CHROME_CAPABILITIES = _CHROME_OPTIONS.to_capabilities()
_CHROME_CAPABILITIES['loggingPrefs'] = {'browser': 'ALL'}
CHROME = make_test_web_driver(Chrome, desired_capabilities=_CHROME_CAPABILITIES)

ALL_DRIVERS = [CHROME]


class NavigationTestCase(StaticLiveServerTestCase, TestCase):
    @classmethod
    def setUpClass(cls):
        super(NavigationTestCase, cls).setUpClass()

        package_path = os.path.dirname(__file__)
        project_path = os.path.dirname(package_path)
        global_screenshots_path = os.path.join(project_path, 'screenshots')
        if not os.path.exists(global_screenshots_path):
            os.mkdir(global_screenshots_path)

        test_suite_dirname = re.sub(r'(.)([A-Z])', r'\1-\2', cls.__name__)
        cls.test_suite_screenshots_path = os.path.join(global_screenshots_path,
                                                       test_suite_dirname).lower()
        if not os.path.exists(cls.test_suite_screenshots_path):
            os.mkdir(cls.test_suite_screenshots_path)

    def screenshot(self, driver, test_case_name, filename):
        screenshots_path = os.path.join(self.test_suite_screenshots_path,
                                        test_case_name.replace('_', '-'))
        if not os.path.exists(screenshots_path):
            os.mkdir(screenshots_path)
        driver.save_screenshot(os.path.join(screenshots_path, filename))

    def walkthrough(self, driver, response, test_case_name=None):
        navigation_handlers = [
            self.navigate_landing,
            self.answer_quantitative_questions,
            self.rate_comments,
            self.answer_qualitative_questions,
            self.provide_personal_information,
        ]

        return all(handler(driver, response, test_case_name)
                   for handler in navigation_handlers)

    def navigate_landing(self, driver, response, test_case_name=None):
        if response:
            driver.get(self.live_server_url + reverse('pcari:landing'))
            if test_case_name:
                self.screenshot(driver, test_case_name, 'landing.png')
            driver.find_element_by_id('next').click()
        return reverse('pcari:quantitative-questions') in driver.current_url

    def answer_quantitative_questions(self, driver, response, test_case_name=None):
        try:
            question_ids = driver.execute_script('return QUESTION_IDS;')
        except WebElement:
            question_ids = []
        finally:
            num_questions = QuantitativeQuestion.objects.filter(active=True).count()
            self.assertEqual(len(question_ids), num_questions)
        scores = response.get('question-ratings', {})

        for question_id in question_ids:
            if test_case_name:
                self.screenshot(driver, test_case_name,
                                'quantitative-question-{0}.png'.format(question_id))

            score = scores.get(question_id, scores.get(str(question_id)))
            if score is None:
                break
            elif score == QuantitativeQuestionRating.SKIPPED:
                driver.find_element_by_id('skip').click()
                continue

            input_element = driver.find_element_by_id('quantitative-input')
            try:
                input_element.set_range_value(score)
            except ValueError as exc:
                self.assertEqual(exc.message, 'not a range element')
                self.assertEqual(input_element.get_attribute('type'), 'number')
                input_element.send_keys(str(score))
            driver.find_element_by_id('submit').click()

        return reverse('pcari:rate-comments') in driver.current_url

    def rate_comments(self, driver, response, test_case_name=None):
        scores = response.get('comment-ratings', {})
        time.sleep(2)  # Wait for force simulation to work

        if test_case_name:
            self.screenshot(driver, test_case_name, 'rate-comments-bloom.png')

        for comment_id, score in scores.iteritems():
            icons = [icon for icon in driver.find_elements_by_tag_name('g')
                     if int(icon.get_attribute('cid')) == int(comment_id)]
            if icons:
                self.assertEqual(len(icons), 1)
                icons[0].find_element_by_tag_name('text').click()

                if score != QuantitativeQuestionRating.SKIPPED:
                    driver.find_element_by_id('quantitative-input').set_range_value(score)

                if test_case_name:
                    self.screenshot(driver, test_case_name,
                                    'rate-comments-{0}.png'.format(comment_id))

                button_id = 'skip' if score == QuantitativeQuestionRating.SKIPPED else 'submit'
                driver.find_element_by_id(button_id).click()

        driver.find_element_by_id('next').click()
        return reverse('pcari:qualitative-questions') in driver.current_url

    def answer_qualitative_questions(self, driver, response, test_case_name=None):
        comment_inputs = driver.find_elements_by_class_name('comment')
        comments = response.get('comments', {})

        for question_id, comment in comments.iteritems():
            text_areas = [comment_input for comment_input in comment_inputs
                          if int(comment_input.get_attribute('question-id')) == int(question_id)]
            if text_areas:
                self.assertEqual(len(text_areas), 1)
                text_areas[0].send_keys(str(comment))

        if test_case_name:
            self.screenshot(driver, test_case_name, 'qualitative-questions.png')

        driver.find_element_by_id('next').click()
        return reverse('pcari:personal-information') in driver.current_url

    def provide_personal_information(self, driver, response, test_case_name=None):
        respondent_data = response.get('respondent-data', {})
        if 'age' in respondent_data:
            driver.find_element_by_id('age').send_keys(str(respondent_data['age']))
        if 'gender' in respondent_data:
            input_element = driver.find_element_by_id('gender')
            select = Select(input_element)
            select.select_by_value(respondent_data['gender'])
            # FIXME: for some reason, using the above selection code does not
            #        trigger the `input` event, which you can verify manually
            #        in Chrome
            driver.execute_script("""$(arguments[0]).trigger('input');""",
                                  input_element)
        if 'province' in respondent_data:
            driver.find_element_by_id('province').send_keys(respondent_data['province'])
        if 'city-or-municipality' in respondent_data:
            input_element = driver.find_element_by_id('city-or-municipality')
            input_element.send_keys(respondent_data['city-or-municipality'])
        if 'barangay' in respondent_data:
            driver.find_element_by_id('barangay').send_keys(respondent_data['barangay'])

        if test_case_name:
            self.screenshot(driver, test_case_name, 'personal-information.png')

        driver.find_element_by_id('next').click()
        driver.find_element_by_id('submit').click()
        return reverse('pcari:peer-responses') in driver.current_url


@tag('slow')
@use_drivers(*ALL_DRIVERS)
class ResponseSubmissionTestCase(NavigationTestCase):
    @classmethod
    def setUpTestData(cls):
        QuantitativeQuestion.objects.create(id=1)
        QuantitativeQuestion.objects.create(id=2)
        QualitativeQuestion.objects.create(id=1)
        Comment.objects.create(id=1, question_id=1, message='Test comment 1',
                               respondent=Respondent.objects.create(id=1))
        Comment.objects.create(id=2, question_id=1, message='Test comment 2',
                               respondent=Respondent.objects.create(id=2))

    def test_complete_submission(self, driver):
        self.assertTrue(self.walkthrough(driver, {
            'question-ratings': {
                1: 2,
                2: QuantitativeQuestionRating.SKIPPED,
            },
            'comment-ratings': {
                1: 9,
                2: 4,
            },
            'comments': {
                1: 'Test comment',
            },
            'respondent-data': {
                'age': 35,
                'gender': 'M',
                'province': 'Test province',
                'city-or-municipality': 'Test city',
                'barangay': 'Test barangay',
            },
        }, 'test_complete_submission'))
        time.sleep(1)

        self.assertEqual(Respondent.objects.count(), 3)
        new_respondent = Respondent.objects.exclude(id__in=[1, 2]).first()
        self.assertEqual(new_respondent.age, 35)
        self.assertEqual(new_respondent.gender, 'M')
        self.assertEqual(new_respondent.location, 'Test province, Test city, Test barangay')
        self.assertEqual(new_respondent.language, 'en')

        self.assertEqual(new_respondent.num_questions_rated, 1)
        self.assertEqual(new_respondent.num_comments_rated, 2)
        self.assertEqual(new_respondent.comments.count(), 1)
        self.assertEqual(new_respondent.comments.first().message, 'Test comment')

        query = QuantitativeQuestionRating.objects.filter(respondent=new_respondent)
        self.assertEqual(query.get(question_id=1).score, 2)
        self.assertEqual(query.get(question_id=2).score, QuantitativeQuestionRating.SKIPPED)

        query = CommentRating.objects.filter(respondent=new_respondent)
        self.assertEqual(query.get(comment_id=1).score, 9)
        self.assertEqual(query.get(comment_id=2).score, 4)
        self.assertEqual(query.count(), CommentRating.objects.count())

        self.assertEqual(Comment.objects.get(respondent=new_respondent).message,
                         'Test comment')

    def test_partial_submission_reset(self, driver):
        response = {
            'question-ratings': {
                1: 7,
                2: 0,
            },
            'comment-ratings': {
                1: QuantitativeQuestionRating.SKIPPED,
                2: 3,
            },
            'comments': {
                1: 'Testing'
            },
        }

        self.assertTrue(self.navigate_landing(driver, response))
        self.assertTrue(self.answer_quantitative_questions(driver, response))
        self.assertTrue(self.rate_comments(driver, response))
        self.assertTrue(self.answer_qualitative_questions(driver, response))

        driver.find_element_by_id('age').send_keys('119')
        driver.back()  # To comment page
        driver.back()  # To bloom page
        driver.back()  # To quantitative question page
        driver.back()  # To landing page

        self.assertIn(reverse('pcari:landing'), driver.current_url)
        self.assertEqual(Respondent.objects.count(), 2)

        self.assertTrue(self.navigate_landing(driver, response))
        time.sleep(1)
        self.assertEqual(Respondent.objects.count(), 3)
        new_respondent = Respondent.objects.exclude(id__in=[1, 2]).first()
        self.assertEqual(new_respondent.age, 119)
        self.assertEqual(new_respondent.gender, '')
        self.assertEqual(new_respondent.location, '(No province), (No city or '
                                                  'municipality), (No barangay)')

        self.assertEqual(new_respondent.num_questions_rated, 2)
        self.assertEqual(new_respondent.num_comments_rated, 1)
        self.assertEqual(new_respondent.comments.count(), 1)

    def test_partial_submission_expiration(self, driver):
        response = {
            'question-ratings': {
                1: 6,
                2: 8,
            },
            'comment-ratings': {
                2: 3,
            },
        }

        self.assertFalse(self.walkthrough(driver, response))
        self.assertIn(reverse('pcari:rate-comments'), driver.current_url)

        driver.refresh()
        driver.spoof_time_change(datetime.timedelta(hours=11, minutes=50))
        driver.execute_script('main();')
        time.sleep(1)
        self.assertEqual(Respondent.objects.count(), 2)

        driver.refresh()
        driver.spoof_time_change(datetime.timedelta(hours=12, minutes=10))
        driver.execute_script('main();')
        time.sleep(1)
        self.assertEqual(Respondent.objects.count(), 3)

        new_respondent = Respondent.objects.exclude(id__in=[1, 2]).first()
        self.assertIsNone(new_respondent.age)
        self.assertEqual(new_respondent.num_questions_rated, 2)
        self.assertEqual(new_respondent.num_comments_rated, 1)
        self.assertEqual(new_respondent.comments.count(), 0)


"""
class AppearanceTestCase(NavigationTestCase):
    def test_translation(self):
        pass


@use_drivers(*ALL_DRIVERS)
class LocalStorageUpdateTestCase(NavigationTestCase):
    pass
"""


class ReusableLiveServerThread(LiveServerThread):
    def _create_server(self):
        return WSGIServer((self.host, self.port), QuietWSGIRequestHandler,
                          allow_reuse_address=True)


@tag('slow')
@use_drivers(*ALL_DRIVERS)
class OfflineTestCase(NavigationTestCase):
    server_thread_class = ReusableLiveServerThread
    port = 8080

    @classmethod
    def setUpTestData(cls):
        QuantitativeQuestion.objects.get_or_create(id=1)
        QuantitativeQuestion.objects.get_or_create(id=2)
        QualitativeQuestion.objects.get_or_create(id=1)
        Respondent.objects.get_or_create(id=1)
        Respondent.objects.get_or_create(id=2)
        Comment.objects.get_or_create(id=1, question_id=1, message='Test comment 1',
                                      respondent_id=1)
        Comment.objects.get_or_create(id=2, question_id=1, message='Test comment 2',
                                      respondent_id=2)

    def assert_no_connection_refused(self, driver):
        for log_entry in driver.get_log('browser'):
            self.assertNotIn('ERR_CONNECTION_REFUSED', log_entry['message'])

    def test_basic_pages_cached(self, driver):
        driver.get(self.live_server_url + reverse('pcari:landing'))
        time.sleep(2)  # Wait for pages to be cached
        self.tearDownClass()

        driver.get(self.live_server_url + reverse('pcari:landing'))
        self.assert_no_connection_refused(driver)
        self.assertTrue(self.walkthrough(driver, {
            'question-ratings': {
                1: 2,
                2: 8,
            },
            'comment-ratings': {
                1: 2,
                2: CommentRating.SKIPPED,
            },
            'comments': {
                1: 'Testing',
            },
            'respondent-data': {
                'age': 20,
            },
        }))

        self.assertEqual(Respondent.objects.count(), 2)
        self.setUpClass()
        time.sleep(1)
        driver.refresh()
        time.sleep(1)
        self.assertEqual(Respondent.objects.count(), 3)
