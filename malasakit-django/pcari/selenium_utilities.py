"""
Utilities for integration testing with Selenium. Includes a
modified webdriver with methods for interacting with UI elements
and displaying browser logs. Also has an abstract test case that
handles setting up and initializing db and webdriver.

"""

import json
from random import choice, randint, sample
import string

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse

from selenium import webdriver
from selenium.webdriver.support.select import Select


class TestDriver(webdriver.Chrome):
    """WebDriver with additional easy-to-use methods for manipulating UI
    elements"""
    # Interfacing with individual UI elements
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
            res = rand_string(20)
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
            'province': rand_string(),
            'city': rand_string(),
            'barangay': rand_string()
        }

        self.set_text_box_val(age_input, personal_info['age'])
        self.set_select_val_by_ind(gender_input, personal_info['gender'])
        self.set_text_box_val(province_input, personal_info['province'])
        self.set_text_box_val(city_input, personal_info['city'])
        self.set_text_box_val(barangay_input, personal_info['barangay'])

        return personal_info

    # Utility stuff

    def print_log(self, log): #pylint: disable=no-self-use
        """Prints a log from driver.get_log."""
        for entry in log:
            print '{:<12} {:<10} {}'.format(
                entry['source'], entry['level'],
                entry['message'])

    @property
    def local_storage(self):
        """
        Fetches the contents of the browser's `localStorage` object.

        Returns:
            The `localStorage` object as a Python `dict`.
        """
        return self.execute_script("""
        var items = {};
        for (var index = 0; index < localStorage.length; index++) {
            var key = localStorage.key(index);
            items[key] = JSON.parse(localStorage.getItem(key));
        }
        return items;
        """)


def rand_string(length=10):
    """Returns a random string of uppercase characters of length n"""
    return ''.join(choice(string.ascii_uppercase) for _ in range(length))

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

    @staticmethod
    def dump_driver_log_on_error(func):
        """Decorator method, if execption occurs in method execution then
        this will print the driver log"""
        def check(self):
            """execute desired function (usually some action on a page)"""
            self.driver.get_log('browser') # purge log before execution
            try:
                func(self)
            except Exception as err:
                print "EXCEPTION ENCOUNTERED, DUMPING TEST DRIVER LOG"
                log = self.driver.get_log('browser')
                self.driver.print_log(log)
                raise err

        return check
