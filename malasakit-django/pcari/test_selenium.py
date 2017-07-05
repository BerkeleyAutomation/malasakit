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
- Clock stuff- throw system clock forward

Tests that we want but are not vital to functionality
- Proper mobile scaling (by testing with smaller window)

Tests that we want but are harder to implement as part of Django test suite:
- LocalStorage is behaving correctly (offline case)
- ServiceWorker works when offline

Architectural thoughts:
Writing multiple levels. Interfacing with a single UI element, responding to a question etc.
"""
import json
from random import choice, randint, sample
import string
import time

from django.db import IntegrityError
from django.test import LiveServerTestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from django.conf import settings

from selenium import webdriver
from selenium.webdriver.support.select import Select

from .models import Respondent
from .models import QuantitativeQuestion, QualitativeQuestion
from .models import Comment, QuantitativeQuestionRating, CommentRating


class TestDriver(webdriver.Chrome):
    """WebDriver with additional easy-to-use methods for manipulating UI
    elements"""
    def __init__(self, desired_capabilities=None, chrome_options=None):
        webdriver.Chrome.__init__(self, chrome_options=chrome_options,
                                  desired_capabilities=desired_capabilities)

    # Interfacing with individual UI elements
    def set_text_box_val(self, element, val):  #pylint: disable=no-self-use
        """Sets a text box to a particular value by sending keystrokes.

        Naively sends keys in, does not check if input has constraints (e.g.
        numbers only).

        Args:
            element: desired input element
            val: any value.
        """
        element.send_keys(val)

    def set_select_val_by_ind(self, element, ind): #pylint: disable=no-self-use
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

        assert isinstance(val, int), "parameter val is not an int"
        assert (val >= min_range and val <= max_range), """val must be between
        %d and %d but it was %d""" % (min_range, max_range, val)

        # assumes we only have one input[type=range] element per view
        script = """$('input[type=range]')
                .val(%s).trigger('input')""" \
                % (val)
        self.execute_script(script)

    # Up one level- individual question-answering in each view
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
        slider = element.find_element_by_css_selector('input[type=range]')
        skip = element.find_element_by_id('skip')
        submit = element.find_element_by_id('submit')

        slider_max = int(slider.get_attribute('max'))

        assert all([val >= -1 and val <= slider_max] for val in history), \
        """history values must be between %d and %d""" % (-1, slider_max)

        for val in history:
            # if we want to change slider value and it's currently -1, we have to
            # hit the skip button
            if val == -1:
                skip.click()
                return # quit early
            else:
                self.set_slider_val(slider, val)
        submit.click()

    # Up one more level- behavior at the view level (i.e. randomly fill out) view
    # and return the responses

    def quant_questions_random_responses(self): #pylint: disable=invalid-name
        """Randomly assigns answers sequences to each quantitative question, by
        setting slider positions of each question multiple times. Returns
        answers in a list of lists where each inner list is the rating sequence
        that was inputted. Assumes driver is at quantitative questions view.
        Includes skipping (-1)."""

        responses = []
        i = 0
        # Keeps answering quantitative questions until there are none left
        # (we've moved onto a new view)
        while "quantitative-questions" in self.current_url:
            # goes and gets the slider bounding div, goes up to capture
            # div that has that and buttons
            question = self.find_element_by_id('answer').find_element_by_xpath('..')
            num_changes = randint(1, 8)
            res_history = sample(range(0, 10), num_changes) # unique

            if i == 0:
                res_history.append(-1)
                # test a skip, -1 will skip the question at the end.

            self.respond_quant_question(question, res_history)
            responses.append(res_history)
            i += 1

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
            res_history = sample(range(1, 10), num_changes) # unique

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
        """Randomly writes responses to a qualitative questions. Returns the
        response as a dict with the key being the 'question-id' attribute.
        Assumes driver is at qualitiative question view."""
        responses = {}

        qual_q_list = self.find_element_by_id('qualitative-questions') \
                          .find_elements_by_tag_name('textarea')

        for question in qual_q_list:
            res = randString(20)
            question_id = question.get_attribute('question-id')
            responses[question_id] = res
            self.set_text_box_val(question, res)

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
            'age': randint(0, 99),
            'gender': randint(0, 2),
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

    # Utility stuff

    def print_log(self, log):
        """Prints a log from driver.get_log."""
        for entry in log:
            print '{:<12} {:<10} {}'.format(
                entry['source'], entry['level'],
                entry['message'])

    def get_local_storage(self, print_leftover=False):
        """Gets browser localStorage and converts to a Python dict. IMPORTANT:
        Purges the log before executing scripts; any other log output that has
        been accumulated will be lost.

        Args:
            print_leftover: default False, whether or not to print log contents
                            still present before getting LocalStorage

        Returns: Dictionary with the same structure as the LocalStorage dict on
                 the client.

        """

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
            s = s.replace("\\", "")
            return s

        leftover = self.get_log('browser')
        if print_leftover:
            print "LEFTOVER IN LOG:"
            self.print_log(leftover) # purges log and displays output

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
        vals = []
        for entry in self.get_log('browser'):
            try:
                vals.append(json.loads(strip_output(entry['message'])))
            except Exception as e:
                print "ERROR IN JSON PARSING"
                print entry['message']
                print strip_output(entry['message'])
                raise e
        for k, v in zip(keys, vals):
            local_storage[k] = v

        return local_storage


def randString(n=10):
    """Returns a random string of uppercase characters of length n"""
    return ''.join(choice(string.ascii_uppercase) for _ in range(n))


class AbstractSeleniumTestCase(StaticLiveServerTestCase):
    """Abstract test case that is inherited from, all Selenium test cases
    share the same ChromeDriver initialization procedure and debugging
    decorators."""

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

    def dump_driver_log_on_error(fn):
        """Decorator method, if execption occurs in method execution then
        this will print the driver log"""
        def check(self):
            # execute desired function (usually some action on a page)
            self.driver.get_log('browser') # purge log before execution
            try:
                fn(self)
            except Exception as e:
                print "EXCEPTION ENCOUNTERED, DUMPING TEST DRIVER LOG"
                log = self.driver.get_log('browser')
                self.driver.print_log(log)
                raise e

        return check


    # enabling decorators for subclasses
    # https://stackoverflow.com/questions/3421337/
    # accessing-a-decorator-in-a-parent-class-from-the-child-in-python
    dump_driver_log_on_error = staticmethod(dump_driver_log_on_error)

class PageLoadTestCase(AbstractSeleniumTestCase):
    """Clickthrough test case, checks for page functionality and LocalStorage
    correctness."""


    """Methods for testing views. Each one should push inputs to corresponding
    key in dictionary self.inputs."""

    @AbstractSeleniumTestCase.dump_driver_log_on_error
    def landing(self):
        print "********* TEST LANDING PAGE ********"
        # check that we're actually on the page
        assert reverse('pcari:landing') in self.driver.current_url

        # self.driver.print_log(self.driver.get_log('browser'))
        self.driver.find_element_by_css_selector("a[href='%s']" % (reverse(
            'pcari:quantitative-questions'
        ))).click()

    @AbstractSeleniumTestCase.dump_driver_log_on_error
    def quant_questions(self):
        print "********* TEST QUANTITATIVE QUESTIONS *********"
        # check that we're actually on the page
        assert reverse('pcari:quantitative-questions') in self.driver.current_url

        self.inputs['quantitative-questions'] = \
                            self.driver.quant_questions_random_responses()

    @AbstractSeleniumTestCase.dump_driver_log_on_error
    def rate_comments(self):
        print "********* TEST COMMENT BLOOM *********"
        # check that we're actually on the page
        assert reverse('pcari:rate-comments') in self.driver.current_url

        self.inputs['rate-comments'] = \
                            self.driver.rate_comments_random_responses()
        # self.driver.print_log(self.driver.get_log('browser'))

        self.driver.find_element_by_css_selector("a[href='%s']" % (
            reverse('pcari:qualitative-questions')
        )).click()

    @AbstractSeleniumTestCase.dump_driver_log_on_error
    def qual_questions(self):
        print "********* TEST QUALTITATIVE QUESTIONS *********"
        # check that we're actually on the page
        assert reverse('pcari:qualitative-questions') in self.driver.current_url

        self.inputs['qualitative-questions'] = \
                                self.driver.qual_questions_random_responses()

        self.driver.find_element_by_css_selector("a[href='%s']" % (
            reverse('pcari:personal-information')
        )).click()

    @AbstractSeleniumTestCase.dump_driver_log_on_error
    def personal_info(self):
        print "********* TEST PERSONAL INFO *********"
        # check that we're actually on the page
        assert reverse('pcari:personal-information') in self.driver.current_url

        self.driver.get("%s%s" % (self.live_server_url,
                                  reverse('pcari:personal-information')))

        self.inputs['personal-info'] = \
                                    self.driver.personal_info_random_responses()


    def check_script_and_local_storage(self):
        """Final check before submission: look for any errors in JavaScript
        that didn't break flow, purge log, grab LocalStorage, and check
        its correctness (against randomized inputs)."""
        print "********* TEST SCRIPT ERRORS AND LOCAL STORAGE *********"

        local_storage = self.driver.get_local_storage()
        current_user = local_storage[local_storage['current']['data']]['data']

        print self.inputs
        print current_user
        # test quant question answers
        for k in current_user['question-ratings'].keys():
            i = int(k) - 1 # keys are 1-indexed and strings
            # score history is disabled for now, so just testing LS score
            # against final element in expected_list
            ls_score = current_user['question-ratings'][k]
            expected_list = self.inputs['quantitative-questions'][i]
            self.assertEqual(ls_score, expected_list[-1],
                             """"question %s:
                expected %s but got %s""" % (k, expected_list[-1], ls_score))
            # self.assertListEqual(ls_list, expected_list,
            #                      msg="""Incorrect history on quant q %s (index
            #                      %s), expected %s but got %s""" % (k, i,
            #                                    expected_list, ls_list))

        # test that comment ratings are identical (hard to get comment ids from UI)
        ls_ratings = current_user['comment-ratings'].values()
        expected_ratings = [r[-1] for r in self.inputs['rate-comments']]
        ls_ratings.sort()
        expected_ratings.sort()
        self.assertListEqual(ls_ratings, expected_ratings,
                             "expected %s, got %s" % (str(expected_ratings),
                                                      str(ls_ratings)))

        # test qual question answers
        for k in current_user['comments'].keys():
            comment = current_user['comments'][k]
            expected_comment = self.inputs['qualitative-questions'][k]
            self.assertEqual(comment, expected_comment)

        # test personal info
        self.assertEqual(current_user['respondent-data']['province'],
                         self.inputs['personal-info']['province'])
        self.assertEqual(current_user['respondent-data']['age'],
                         self.inputs['personal-info']['age'])
        self.assertEqual(current_user['respondent-data']['city-or-municipality'],
                         self.inputs['personal-info']['city'])
        self.assertEqual(current_user['respondent-data']['barangay'],
                         self.inputs['personal-info']['barangay'])

    @AbstractSeleniumTestCase.dump_driver_log_on_error
    def submission(self):
        """Submits the response. """
        print "******** TEST RESPONSE SUBMISSION ********"
        before = Respondent.objects.count()
        # click the next button, should pull up a popup
        self.driver.find_element_by_css_selector('a[href="%s"]' % reverse(
            'pcari:peer-responses'
        )).click()
        self.driver.find_element_by_id('submit').click()
        self.assertEqual(Respondent.objects.count(), before + 1)
        # we shouldn't need to test the correctness of the response in the db
        # because that is already tested in the views

    def test_flow_local_storage(self):
        """Clicks through views in appropriate order"""
        print ""
        self.landing()
        self.quant_questions()
        self.rate_comments()
        self.qual_questions()
        self.personal_info()
        self.check_script_and_local_storage()
        self.submission()