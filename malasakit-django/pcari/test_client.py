import logging
import os
import time

from django.test import tag
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.shortcuts import reverse
from selenium.webdriver import Chrome, ChromeOptions, Firefox
from selenium.webdriver.common.keys import Keys
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
    def wrap_test(test):
        def test_wrapper(self):
            for test_driver_cls in test_drivers:
                driver = test_driver_cls()
                driver.start()
                test(self, driver)
                driver.stop()
        return test_wrapper
    return wrap_test


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


class NavigationTestCase(StaticLiveServerTestCase):
    def walkthrough(self, driver, response):
        navigation_handlers = [
            self.pass_landing,
            self.answer_quantitative_questions,
            self.rate_comments,
        ]

        return all(handler(driver, response) for handler in navigation_handlers)

    def pass_landing(self, driver, response):
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
        bloom_icons = driver.find_elements_by_tag_name('g')
        scores = response.get('comment-ratings', {})

        for comment_id, score in scores.iteritems():
            icons = [icon for icon in bloom_icons
                     if int(icon.get_attribute('cid')) == comment_id]
            if len(icons) > 0:
                self.assertEqual(len(icons), 1)
                icons[0].click()

                if score == QuantitativeQuestionRating.SKIPPED:
                    driver.find_element_by_id('skip').click()
                else:
                    driver.find_element_by_id('quantitative-input').set_range_value(score)
                    driver.find_element_by_id('submit').click()

        driver.find_element_by_id('next').click()
        return reverse('pcari:qualitative-questions') in driver.current_url

    @use_drivers(*ALL_DRIVERS)
    def test_test(self, driver):
        QuantitativeQuestion.objects.create(id=1)
        Comment.objects.create(id=1, message='sdf', respondent=Respondent.objects.create(), question=QualitativeQuestion.objects.create())
        print(self.walkthrough(driver, {'question-ratings': {1: 6}, 'comment-ratings': {1: -1}}))


"""
class NavigationTestCase(StaticLiveServerTestCase):
    @use_drivers(*WEB_DRIVERS)
    def test_complete_walkthrough(self, driver):
        self.questions = [QuantitativeQuestion.objects.create() for _ in range(8)]
        driver.get(self.live_server_url + reverse('pcari:landing'))
        html = driver.find_element_by_tag_name('html')
        driver.find_element_by_id('next').click()
        for _ in range(len(self.questions)):
            self.assertIn(reverse('pcari:quantitative-questions'), driver.current_url)
            driver.find_element_by_id('submit').click()
        self.assertIn(reverse('pcari:rate-comments'), driver.current_url)


@tag('slow')
class OfflineTestCase(StaticLiveServerTestCase):
    TIMEOUT = 4.0  # in seconds

    @classmethod
    def setUpClass(cls):
        super(OfflineTestCase, cls).setUpClass()

        package_path = os.path.dirname(__file__)
        project_path = os.path.dirname(package_path)
        cls.screenshots_path = os.path.join(project_path, 'testing-screenshots')
        if not os.path.exists(cls.screenshots_path):
            os.mkdir(cls.screenshots_path)

    @use_drivers(*WEB_DRIVERS)
    def test_offline(self, driver):
        driver.get(self.live_server_url + reverse('pcari:landing'))
        print driver.get_log('browser')

        time.sleep(self.TIMEOUT)

        self.tearDownClass()

        driver.get(self.live_server_url + reverse('pcari:landing'))
        print driver.get_log('browser')
        driver.save_screenshot(os.path.join(self.screenshots_path, 'landing.png'))
        print driver.local_storage

        self.setUpClass()

        driver.get(self.live_server_url + reverse('pcari:landing'))
        print driver.get_log('browser')
"""
