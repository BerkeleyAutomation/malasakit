from django.db import IntegrityError
from django.test import LiveServerTestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse

from django.conf import settings

import json

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

        script = """$('input.quantitative-input[target-id=%s]')
                .val(%s).trigger('change')""" \
                % (element.get_attribute("target-id"), val)
        self.execute_script(script)

    """Up one level- individual question-answering in each view"""

    def respond_comment(self, element, history):
        """Given a comment bubble element, clicks it and sets the slider to a
        given value.

        Assumption: clicking a comment pops up a hover div with a slider,
        submit and skip buttons.

        Will throw an error if the click is unsuccessful

        Args:
            element: the bubble to be clicked
            history: list of ints, all must fall between -1 (skipped) and slider
                     max. Slider will be moved around multiple times.
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

        assert all([val >= -1 and val <= slider_max] for val in history), \
        """history values must be between %d and %d""" % (-1, slider_max)

        assert (-1 not in history or history.index(-1) == -1
                or history.index(-1) + 1 == len(history)), """history must only
                have -1s at end if they exist."""
        # skipping a question knocks it out

        for val in history:
            if val == -1:
                skip.click()
                return # quit early. this is suboptimal, should write better.
            else:
                self.set_slider_val(slider, val)
        submit.click()

    def respond_quant_question(self, element, history):
        """Given a quantitative question bounding element (contains both the
        slider and the skip switch), responds with a given value.

        Assumes that for each quantitative question, the slider is an input
        tag with class 'quantitative-input' and the button is located inside
        a label tag with class 'switch'.

        Args:
            element: bounding element containing both slider and skip switch
            history: list of ints, all must fall between -1 (skipped) and slider
                     max. Slider will be moved around multiple times.
        """
        slider = element.find_element_by_class_name('quantitative-input')
        skip = element.find_element_by_class_name('switch')

        slider_max = int(slider.get_attribute('max'))

        assert all([val >= -1 and val <= slider_max] for val in history), \
        """history values must be between %d and %d""" % (-1, slider_max)

        for val in history:
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
        """Randomly assigns answers sequences to each quantitative question, by
        setting slider positions of each question multiple times. Returns
        answers in a list of lists where each inner list is the rating sequence
        that was inputted. Assumes driver is at quantitative questions view.
        Includes skipping (-1)."""

        quant_q_list = self.find_element_by_id('quantitative-questions') \
                           .find_elements_by_tag_name('li')

        print("number of quantitative questions:", len(quant_q_list))

        responses = []
        for q in quant_q_list:
            num_changes = randint(1, 8)
            res_history = [randint(-1, 9) for _ in range(num_changes)]
            self.respond_quant_question(q, res_history)
            responses.append(res_history)

        return responses

    def rate_comments_random_responses(self):
        """Randomly selects some comments and responds to them. Assumes driver
        is at rate comments view. Returns a list of comment ratings.

        Assumes comment bubbles are in <image> tags, which can be clicked.
        TODO: Figure out a way to know which comments were responded to"""

        bubbles = self.find_elements_by_tag_name('image')
        count = randint(2, len(bubbles)) # rate a random number of comments
        responses = []

        for i in range(count):
            # randomly draw a comment bubble from the list and respond to it
            num_changes = randint(1, 8)
            res_history = [randint(0, 9) for _ in range(num_changes)]

            if i == 0:
                res_history.append(-1)
                # test a skip, -1 will skip the question at the end.

            self.respond_comment(choice(bubbles), res_history)
            responses.append(res_history)
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
        city_input = self.find_element_by_id('city-or-municipality')
        barangay_input = self.find_element_by_id('barangay') # input text box

        personal_info = {
            'age': randint(0,99),
            'gender': randint(0,2),
            'province': randString(),
            'city': randString(),
            'barangay': randString()
        }

        self.set_text_box_val(age_input, personal_info['age'])
        self.set_select_val_by_ind(gender_input, personal_info['gender'])
        self.set_text_box_val(province_input, personal_info['province'])
        self.set_text_box_val(city_input, personal_info['city'])
        self.set_text_box_val(barangay_input, personal_info['barangay'])

        return personal_info

    """Utility stuff"""

    def print_log(self, log):
        """Prints a log from driver.get_log."""
        for entry in log:
            print '{:<12} {:<10} {}'.format(
                entry['source'], entry['level'],
                entry['message'])

    def get_local_storage(self):
        """Gets browser localStorage and converts to a Pythong dict"""

        def strip_output(s):
            """Removes console stuff and redundant backslashes from
            console log strings.

            The 'message' field of a log entry that Selenium obtains from
            ChromeDriver is not just what is printed to the console- it includes
            other info about line numbers and sources. Additionally, strings
            are sometimes escaped when they need not be. This makes it difficult
            to parse out JSON strings that we obtain from LocalStorage.
            """
            s = s[s.find("\"") + 1:s.rfind("\"")]
            s = s.replace("\\","")
            return s

        script_get_ls_keys = """Object.keys(localStorage).forEach(function(s){
            console.log(s);
        })"""

        script_get_ls_values = """Object.values(localStorage).
        forEach(function (s) {
            console.log(s)
        })"""

        local_storage = {}
        self.execute_script(script_get_ls_keys)
        keys = [strip_output(entry['message']) \
                for entry in self.get_log('browser')]

        self.execute_script(script_get_ls_values)
        vals = [json.loads(strip_output(entry['message'])) \
                for entry in self.get_log('browser')]

        for k, v in zip(keys, vals):
            local_storage[k] = v

        return local_storage


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

        # Initialize dictionary to keep track of randomized inputs (organized
        # by view) These will be checked against the database/LocalStorage.
        self.inputs = {
            'quantitative-questions': None,
            'rate-comments': None,
            'qualitative-questions': None,
            'personal-information': None
        }


        # Initialize with options for ChromeDriver
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument('window-size=480x800')

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

    """Methods for testing views. Each one should push inputs to corresponding
    key in dictionary self.inputs."""

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

        self.inputs['quantitative_questions'] = \
                            self.driver.quant_questions_random_responses()

        self.driver.print_log(self.driver.get_log('browser'))
        self.driver.get_screenshot_as_file('quant-questions.png')
        self.driver.find_element_by_css_selector("a[href='%s']" % (reverse(
            'pcari:rate-comments'
        ))).click()

    def rate_comments(self):
        print "********* TEST COMMENT BLOOM *********"
        # check that we're actually on the page
        assert reverse('pcari:rate-comments') in self.driver.current_url

        self.inputs['rate-comments'] = \
                            self.driver.rate_comments_random_responses()
        self.driver.print_log(self.driver.get_log('browser'))

        self.driver.get_screenshot_as_file('rate-comments.png')

        self.driver.find_element_by_css_selector("a[href='%s']" % (
            reverse('pcari:qualitative-questions')
        )).click()

    def qual_questions(self):
        print "********* TEST QUALTITATIVE QUESTIONS *********"
        # check that we're actually on the page
        assert reverse('pcari:qualitative-questions') in self.driver.current_url

        self.inputs['qualitative-questions'] = \
                                self.driver.qual_questions_random_responses()

        self.driver.print_log(self.driver.get_log('browser'))
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

        self.inputs['personal-info'] = \
                                    self.driver.personal_info_random_responses()

        self.driver.print_log(self.driver.get_log('browser'))
        self.driver.get_screenshot_as_file('personal-info.png')

    def test_flow_local_storage(self):
        """Clicks through views in appropriate order"""
        self.landing()
        self.quant_questions()
        self.rate_comments()
        self.qual_questions()
        self.personal_info()

        print self.inputs
        local_storage = self.driver.get_local_storage()
        current_user = local_storage[local_storage['current']['data']]
        print current_user

        # test quantitative responses
