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
    def wrap_test_suite(test_suite):
        for name in dir(test_suite):
            if name.startswith('test'):
                obj = getattr(test_suite, name)
                if isinstance(obj, types.MethodType):
                    for index, test_driver_cls in enumerate(test_drivers):
                        name = obj.__name__ + '_' + str(index)
                        def test_wrapper(self):
                            driver = test_driver_cls()
                            obj(self, driver)
                        test_wrapper.__name__ = name
                        setattr(test_suite, name, test_wrapper)
                    delattr(test_suite, obj.__name__)
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
    return TestWebDriver


_CHROME_OPTIONS = ChromeOptions()
_CHROME_OPTIONS.add_argument('headless')
CHROME = make_test_web_driver(Chrome, desired_capabilities=_CHROME_OPTIONS.to_capabilities())

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

        test_case_dirname = re.sub(r'(.)([A-Z])', r'\1-\2', cls.__name__)
        cls.test_case_screenshots_path = os.path.join(global_screenshots_path,
                                                      test_case_dirname).lower()

    def screenshot(self, driver, filename):
        if not os.path.exists(self.test_case_screenshots_path):
            os.mkdir(self.test_case_screenshots_path)
        driver.save_screenshot(os.path.join(self.test_case_screenshots_path, filename))

    def walkthrough(self, driver, response, take_screenshots=False):
        navigation_handlers = [
            self.navigate_landing,
            self.answer_quantitative_questions,
            self.rate_comments,
            self.answer_qualitative_questions,
            self.provide_personal_information,
        ]

        if take_screenshots:
            def enable_screenshot_capture(navigation_handler):
                def navigation_handler_wrapper(driver, response):
                    filename = navigation_handler.__name__.replace('_', '-') + '.png'
                    self.screenshot(driver, filename)
                    return navigation_handler(driver, response)
                return navigation_handler_wrapper
            navigation_handlers = [enable_screenshot_capture(handler)
                                   for handler in navigation_handlers]

        return all(handler(driver, response) for handler in navigation_handlers)

    def navigate_landing(self, driver, response):
        if response:
            driver.get(self.live_server_url + reverse('pcari:landing'))
            driver.find_element_by_id('next').click()
        return reverse('pcari:quantitative-questions') in driver.current_url

    def answer_quantitative_questions(self, driver, response):
        try:
            question_ids = driver.execute_script('return QUESTION_IDS;')
        except WebElement:
            question_ids = []
        finally:
            num_questions = QuantitativeQuestion.objects.filter(active=True).count()
            self.assertEqual(len(question_ids), num_questions)
        scores = response.get('question-ratings', {})

        for question_id in question_ids:
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

    def rate_comments(self, driver, response):
        scores = response.get('comment-ratings', {})

        for comment_id, score in scores.iteritems():
            icons = [icon for icon in driver.find_elements_by_tag_name('g')
                     if int(icon.get_attribute('cid')) == int(comment_id)]
            if icons:
                self.assertEqual(len(icons), 1)
                icons[0].click()

                if score == QuantitativeQuestionRating.SKIPPED:
                    driver.find_element_by_id('skip').click()
                else:
                    driver.find_element_by_id('quantitative-input').set_range_value(score)
                    driver.find_element_by_id('submit').click()

        driver.find_element_by_id('next').click()
        return reverse('pcari:qualitative-questions') in driver.current_url

    def answer_qualitative_questions(self, driver, response):
        comment_inputs = driver.find_elements_by_class_name('comment')
        comments = response.get('comments', {})

        for question_id, comment in comments.iteritems():
            text_areas = [comment_input for comment_input in comment_inputs
                          if int(comment_input.get_attribute('question-id')) == int(question_id)]
            if text_areas:
                self.assertEqual(len(text_areas), 1)
                text_areas[0].send_keys(str(comment))

        driver.find_element_by_id('next').click()
        return reverse('pcari:personal-information') in driver.current_url

    def provide_personal_information(self, driver, response):
        respondent_data = response.get('respondent-data', {})
        if 'age' in respondent_data:
            driver.find_element_by_id('age').send_keys(str(respondent_data['age']))
        if 'gender' in respondent_data:
            select = Select(driver.find_element_by_id('gender'))
            select.select_by_value(respondent_data['gender'])
        if 'province' in response:
            driver.find_element_by_id('province').send_keys(respondent_data['province'])
        if 'city-or-municipality' in response:
            input_element = driver.find_element_by_id('city-or-municipality')
            input_element.send_keys(respondent_data['city-or-municipality'])
        if 'barangay' in response:
            driver.find_element_by_id('barangay').send_keys(respondent_data['barangay'])

        driver.find_element_by_id('next').click()
        driver.find_element_by_id('submit').click()
        return reverse('pcari:peer-responses') in driver.current_url


def spoof_time_change(driver, time_change):
    delta = int(1000*time_change.total_seconds())
    driver.execute_script("""
    Date.prototype._getTime = Date.prototype.getTime;
    Date.prototype.getTime = function() {
        return {delta} + this._getTime();
    };
    """.format(delta))


@tag('slow')
@use_drivers(*ALL_DRIVERS)
class ResponseSubmissionTestCase(NavigationTestCase):
    @classmethod
    def setUpTestData(cls):
        QuantitativeQuestion.objects.create(id=1)
        QuantitativeQuestion.objects.create(id=2)
        QualitativeQuestion.objects.create(id=1)
        Comment.objects.create(id=1, question_id=1,
                               respondent=Respondent.objects.create(id=1))
        Comment.objects.create(id=2, question_id=1,
                               respondent=Respondent.objects.create(id=2))

    def test_complete_full_submission(self, driver):
        self.assertTrue(self.walkthrough(driver, {
            'question-ratings': {
                1: 2,
                2: QuantitativeQuestionRating.SKIPPED,
            },
            'comment-ratings': {
                1: 5,
                2: 9,
            },
            'comments': {
                1: 'Testing',
            },
            'respondent-data': {
                'age': 31,
            },
        }))





"""
@use_drivers(*ALL_DRIVERS)
class LocalStorageUpdateTestCase(NavigationTestCase):
    pass


class ReusableLiveServerThread(LiveServerThread):
    def _create_server(self):
        return WSGIServer((self.host, self.port), QuietWSGIRequestHandler,
                          allow_reuse_address=True)


@tag('slow')
@use_drivers(*ALL_DRIVERS)
class OfflineTestCase(NavigationTestCase):
    server_thread_class = ReusableLiveServerThread
    port = 8080

    DELAY = 4.0  # in seconds

    @classmethod
    def setUpTestData(cls):
        QuantitativeQuestion.objects.create(id=1)
        QuantitativeQuestion.objects.create(id=2)
        QualitativeQuestion.objects.create(id=1)
        Comment.objects.create(question_id=1,
                               respondent=Respondent.objects.create(id=1))
        Comment.objects.create(question_id=1,
                               respondent=Respondent.objects.create(id=2))

    def assert_no_connection_refused(self, driver):
        for log_entry in driver.get_log('browser'):
            self.assertNotIn('ERR_CONNECTION_REFUSED', log_entry['message'])

    @use_drivers(*ALL_DRIVERS)
    def test_basic_pages_cached(self, driver):
        driver.get(self.live_server_url + reverse('pcari:landing'))
        time.sleep(2)  # Wait for pages to be cached
        self.tearDownClass()

        response = {
            'question-ratings': {
                1: r,
                2: 1,
            },
        }

        driver.get(self.live_server_url + reverse('pcari:landing'))
        self.assert_no_connection_refused(driver)
        self.walkthrough(driver, response, True)

        self.setUpClass()
        # print self.live_server_url
"""
