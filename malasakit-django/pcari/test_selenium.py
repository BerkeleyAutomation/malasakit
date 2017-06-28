from django.db import IntegrityError
from django.test import LiveServerTestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse

from django.conf import settings

from random import choice, randint
import string

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
- Changing language does not remove user input
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
    def __init__(self, desired_capabilities=None,chrome_options=None):
        webdriver.Chrome.__init__(self, chrome_options=chrome_options,
                                  desired_capabilities=desired_capabilities)

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

        Assumption: clicking a comment pops up a hover div with a slider,
        submit and skip buttons.

        Will throw an error if the click is unsuccessful

        Args:
            element: the bubble to be clicked
            val: int, must fall between -1 (skipped) and slider max
        """
        # Click the bubble
        element.click()
        # attempt to find element with class 'modal-container'- this is the
        # hover div
        hover_div = self.find_element_by_class_name('modal-container')

        slider = hover_div.find_element_by_class_name('quantitative-input')
        submit = hover_div.find_element_by_id('submit')
        skip = hover_div.find_element_by_id('skip')

        slider_max = int(slider.get_attribute('max'))

        assert (val >= -1 and val <= slider_max), """val must be between
        %d and %d but it was %d""" % (-1, slider_max, val)

        if val == -1:
            skip.click()
        else:
            self.set_slider_val(slider, val)
            submit.click()

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

        return responses

    def rate_comments_random_responses(self):
        """Randomly selects some comments and responds to them. Assumes driver
        is at rate comments view. Returns a list of comment ratings.

        Assumes comment bubbles are in <image> tags, which can be clicked.
        TODO: Figure out a way to know which comments were responded to"""

        bubbles = self.find_elements_by_tag_name('image')
        count = randint(2, len(bubbles)) # rate a random number of comments
        responses = []

        for _ in range(count):
            # randomly draw a comment bubble from the list and respond to it
            res = randint(-1,9)
            responses.append(res)
            self.respond_comment(choice(bubbles), res)
            # because responding to one redraws all, we need to "refresh" and
            # pull from the DOM again
            bubbles = self.find_elements_by_tag_name('image')

        return responses

    def qual_questions_random_responses(self):
        """Randomly writes a response to a qualitative question. Returns the
        response. Assumes driver is at qualitiative question view."""
        responses = []

        qual_q_list = self.find_element_by_id('qualitative-questions') \
                          .find_elements_by_tag_name('textarea')

        for q in qual_q_list:
            res = randString(20)
            responses.append(res)
            self.set_text_box_val(q, res)

        return responses

    def personal_info_random_responses(self):
        """Randomly assigns answers to personal information questions-
        age, gender, province, and barangay. Assumes driver is at
        personal information view. Returns a dict where each key is each
        attribute"""
        age_input = self.find_element_by_id('age') # number-only input text box
        gender_input = self.find_element_by_id('gender') # dropdown
        province_input = self.find_element_by_id('province') # dropdown
        barangay_input = self.find_element_by_id('barangay') # input text box

        personal_info = {
            'age': randint(0,99),
            'gender': randint(0,2),
            'province': randint(0, 50),
            'barangay': randString()
        }

        self.set_text_box_val(age_input, personal_info['age'])
        self.set_select_val_by_ind(gender_input, personal_info['gender'])
        self.set_select_val_by_ind(province_input, personal_info['province'])
        #TODO: how many?
        self.set_text_box_val(barangay_input, personal_info['barangay'])

        return personal_info

    """Utility stuff"""

    def print_log(self, log):
        """Prints a log from driver.get_log."""
        for entry in log:
            print '{:<12} {:<10} {}'.format(
                entry['source'], entry['level'],
                entry['message'])


def randString(n=10):
    """Returns a random string of uppercase characters of length n"""
    return ''.join(choice(string.ascii_uppercase) for _ in range(n))



class PageLoadTestCase(StaticLiveServerTestCase):
    fixtures = ['selenium-questions.yaml', 'selenium-users.yaml']

    def setUp(self):
        """Selenium setup goes here; running headless Chrome"""
        # Concern: localStorage and ServiceWorker stuff may persist
        # between tests so we might want to initialize new driver
        # Less of an issue because one test case (class) is only supposed
        # to test one thing

        # Initialize with options for ChromeDriver
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument('window-size=480x720')

        # Convert to general DesiredCapabilities object
        capabilities = options.to_capabilities()
        capabilities['loggingPrefs'] = {
            'driver': 'INFO',
            'browser': 'INFO'
        }
        # in order to capture normal console.log output

        self.driver = TestDriver(desired_capabilities=capabilities)
        self.driver.get("%s%s" % (self.live_server_url,
                                  reverse("pcari:landing")))


    def landing(self):
        print "********* TEST LANDING PAGE ********"
        # check that we're actually on the page
        assert reverse('pcari:landing') in self.driver.current_url

        self.driver.print_log(self.driver.get_log('browser'))
        self.driver.get_screenshot_as_file('landing.png')
        self.driver.find_element_by_css_selector("a[href='%s']" % (reverse(
            'pcari:quantitative-questions'
        ))).click()

    def quant_questions(self):
        print "********* TEST QUANTITATIVE QUESTIONS *********"
        # check that we're actually on the page
        assert reverse('pcari:quantitative-questions') in self.driver.current_url

        responses = self.driver.quant_questions_random_responses()

        self.driver.print_log(self.driver.get_log('browser'))
        print(responses)
        self.driver.get_screenshot_as_file('quant-questions.png')
        self.driver.find_element_by_css_selector("a[href='%s']" % (reverse(
            'pcari:rate-comments'
        ))).click()

    def rate_comments(self):
        print "********* TEST COMMENT BLOOM *********"
        # check that we're actually on the page
        assert reverse('pcari:rate-comments') in self.driver.current_url

        comments_rated = self.driver.rate_comments_random_responses()
        self.driver.print_log(self.driver.get_log('browser'))
        print(comments_rated)

        self.driver.get_screenshot_as_file('rate-comments.png')

        self.driver.find_element_by_css_selector("a[href='%s']" % (
            reverse('pcari:qualitative-questions')
        )).click()

    def qual_questions(self):
        print "********* TEST QUALTITATIVE QUESTIONS *********"
        # check that we're actually on the page
        assert reverse('pcari:qualitative-questions') in self.driver.current_url

        qual_responses = self.driver.qual_questions_random_responses()

        self.driver.print_log(self.driver.get_log('browser'))
        print(qual_responses)
        self.driver.get_screenshot_as_file('qual-questions.png')

        self.driver.find_element_by_css_selector("a[href='%s']" % (
            reverse('pcari:personal-information')
        )).click()

    def personal_info(self):
        print "********* TEST PERSONAL INFO *********"
        # check that we're actually on the page
        assert reverse('pcari:personal-information') in self.driver.current_url

        self.driver.get("%s%s" % (self.live_server_url,
                             reverse('pcari:personal-information')))

        personal_data = self.driver.personal_info_random_responses()

        self.driver.print_log(self.driver.get_log('browser'))
        print(personal_data)
        self.driver.get_screenshot_as_file('personal-info.png')

    def test_urls(self):
        """Clicks through views in appropriate order"""
        self.landing()
        self.quant_questions()
        self.rate_comments()
        self.qual_questions()
        self.personal_info()
