from django.db import IntegrityError
from django.test import LiveServerTestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse

from django.conf import settings

from random import randint

from .models import Respondent
from .models import QuantitativeQuestion, QualitativeQuestion
from .models import Comment, QuantitativeQuestionRating, CommentRating

from selenium import webdriver
from selenium.webdriver.support.select import Select


"""
Integration tests using Selenium.
Drawing inspiration from
https://docs.djangoproject.com/en/1.10/topics/testing/tools/#liveservertestcase

Tests to include:
- Loading and clicking through webpage
- Language works
- Bloom works
- LocalStorage is behaving correctly (online case)
- ServiceWorker is registered

Tests that we want but are not vital to functionality
- Proper mobile scaling (by testing with smaller window)

Tests that we want but are harder to implement as part of Django test suite:
- LocalStorage is behaving correctly (offline case)
- ServiceWorker works when offline

Architectural thoughts:
Writing multiple levels. Interfacing with a single UI element, responding to a question etc.
"""

class TestDriver(webdriver.Chrome):
    """WebDriver with additional easy-to-use methods for manipulating UI
    elements"""
    def __init__(self, options):
        webdriver.Chrome.__init__(self, chrome_options=options)

    """Interfacing with individual UI elements"""

    def set_text_box_val(self, element, val):
        """Sets a text box to a particular value by sending keystrokes.

        Naively sends keys in, does not check if input has constraints (e.g.
        numbers only).

        Args:
            element: desired input element
            val: any value.
        """
        element.send_keys(val)

    def set_select_val_by_ind(self, element, ind):
        """Sets a select element's value to the option at a particular index.

        Args:
            element: desired select element
            ind: int of desired index (between 0 and num_options - 1)
        """
        element = Select(element)
        element.select_by_index(ind)

    def set_slider_val(self, element, val):
        """Sets a slider (input[type=range]) to a particular value

        This is done by executing JavaScript instead of simulating clicks.
        Error handling is done here because JavaScript will just set an
        overflowing value to max or min.

        Args:
            element: desired range element
            val: int, must fall in between the range element's
                 min and max
        """

        assert element.get_attribute('type') == 'range', \
        'element type is not \'range\', %s' % element.get_attribute('type')

        min_range = int(element.get_attribute('min'))
        max_range = int(element.get_attribute('max'))

        assert type(val) == int, "parameter val is not an int"
        assert (val >= min_range and val <= max_range), """val must be between
        %d and %d but it was %d""" % (min_range, max_range, val)

        script = "$('input.quantitative-input[target-id=%s]').val(%s)" \
        % (element.get_attribute("target-id"), val)
        self.execute_script(script)

    """Up one level- individual question-answering in each view"""

    def respond_comment(self, element, val):
        """Given a comment bubble element, clicks it and sets the slider to a
        given value.

        TODO: Fix PCA in test fixtures before implementing"""
        pass

    def respond_quant_question(self, element, val):
        """Given a quantitative question bounding element (contains both the
        slider and the skip switch), responds with a given value.

        Assumes that for each quantitative question, the slider is an input
        tag with class 'quantitative-input' and the button is located inside
        a label tag with class 'switch'.

        Args:
            element: bounding element containing both slider and skip switch
            val: int, must fall between -1 (skipped) and slider max
        """
        slider = element.find_element_by_class_name('quantitative-input')
        skip = element.find_element_by_class_name('switch')

        slider_max = int(slider.get_attribute('max'))

        assert (val >= -1 and val <= slider_max), """val must be between
        %d and %d but it was %d""" % (-1, slider_max, val)

        # if we want to change slider value and it's currently -1, we have to
        # hit the skip button
        if not slider.is_enabled():
            skip.click()

        if val == -1:
            skip.click()
        else:
            self.set_slider_val(slider, val)

    """Up one more level- behavior at the view level (i.e. randomly fill out)
    view and return the responses"""

    def quant_questions_random_responses(self):
        """Randomly assigns answers to each quantitative question, and returns
        the answers in a list. Assumes driver is at quantitative questions view.
        Includes skipping (-1)."""

        quant_q_list = self.find_element_by_id('quantitative-questions') \
        .find_elements_by_tag_name('li')

        print("number of quantitative questions:", len(quant_q_list))

        responses = []
        for q in quant_q_list:
            res = randint(-1, 9)
            responses.append(res)
            self.respond_quant_question(q, res)

        self.get_screenshot_as_file('qq.png')
        return responses

    def rate_comments_random_responses(self):
        """Randomly selects some comments and responds to them."""
        pass


class PageLoadTestCase(StaticLiveServerTestCase):
    fixtures = ['questions.yaml', 'user-generated.yaml']

    def setUp(self):
        """Selenium setup goes here; running headless Chrome"""
        # Concern: localStorage and ServiceWorker stuff may persist
        # between tests so we might want to initialize new driver

        # options = webdriver.ChromeOptions()
        # options.add_argument('headless')
        # options.add_argument('window-size=720x960')
        # self.driver = webdriver.Chrome(chrome_options=options)

    def test_quant(self):
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument('window-size=720x960')
        driver = TestDriver(options=options)

        driver.get("%s%s" % (self.live_server_url,
                             reverse('pcari:quantitative-questions')))
        # driver.get_screenshot_as_file('qq.png')
        responses = driver.quant_questions_random_responses()
        print(responses)


    def test_bloom(self):
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument('window-size=720x960')
        driver = TestDriver(options=options)

        driver.get("%s%s" % (self.live_server_url,
                             reverse('pcari:rate-comments')))
        driver.get_screenshot_as_file('bloom.png')
        print(driver.get_log('browser'))


    # def test_basic_flow(self):
    #     """Loads landing page and attempts to proceed through the app
    #     as normal, creating random responses. Checks for successful
    #     submission."""

    #     # How many respondents are in the db?
    #     respondent_count = Respondent.objects.count()

    #     # Load Landing Page
    #     self.driver.get("%s%s" % (self.live_server_url,
    #                               reverse('pcari:landing')))
    #     self.driver.get_screenshot_as_file('landing.png')

    #     # Begin Survey (Advance to Personal Information
    #     begin_button = self.driver.find_element_by_css_selector("a[href='%s']"
    #                                 % (reverse('pcari:personal-information')))
    #     begin_button.click()
    #     self.driver.get_screenshot_as_file('personal-info.png')


    #     # Advance to Quantiatative Questions
    #     quant_button = self.driver.find_element_by_css_selector("a[href='%s']"
    #                                 % (reverse('pcari:quantitative-questions')))
    #     quant_button.click()
    #     self.driver.get_screenshot_as_file('quant-qs.png')
