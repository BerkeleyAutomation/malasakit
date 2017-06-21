from django.db import IntegrityError
from django.test import LiveServerTestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse

from django.conf import settings

from .models import Respondent
from .models import QuantitativeQuestion, QualitativeQuestion
from .models import Comment, QuantitativeQuestionRating, CommentRating

from selenium import webdriver


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
"""

class PageLoadTestCase(StaticLiveServerTestCase):
    fixtures = ['questions.yaml', 'user-generated.yaml']

    def setUp(self):
        """Selenium setup goes here; running headless Chrome"""
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument('window-size=720x960')
        settings.DEBUG = True
        self.driver = webdriver.Chrome(chrome_options=options)

    def test_basic_flow(self):
        """Loads landing page and attempts to proceed through the app
        as normal, creating random responses. Checks for successful
        submission."""

        # How many respondents are in the db?
        respondent_count = Respondent.objects.count()

        # Load Landing Page
        self.driver.get("%s%s" % (self.live_server_url,
                                  reverse('pcari:landing')))
        self.driver.get_screenshot_as_file('landing.png')

        # Begin Survey (Advance to Personal Information
        begin_button = self.driver.find_element_by_css_selector("a[href='%s']"
                                    % (reverse('pcari:personal-information')))
        begin_button.click()
        self.driver.get_screenshot_as_file('personal-info.png')


        # Advance to Quantiatative Questions
        quant_button = self.driver.find_element_by_css_selector("a[href='%s']"
                                    % (reverse('pcari:quantitative-questions')))
        quant_button.click()
        self.driver.get_screenshot_as_file('quant-qs.png')
