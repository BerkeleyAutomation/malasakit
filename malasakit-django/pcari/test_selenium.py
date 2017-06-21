from django.db import IntegrityError
from django.test import LiveServerTestCase, Client
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse

from django.conf import settings

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
        settings.DEBUG = True
        self.driver = webdriver.Chrome(chrome_options=options)

    def test_load_landing(self):

        print settings.DEBUG
        print self.live_server_url + "/landing"

        self.driver.get("%s%s" % (self.live_server_url, "/landing/"))
        self.driver.implicitly_wait(10)
        self.driver.get_screenshot_as_file('landing.png')
        for entry in self.driver.get_log("browser"):
            print entry
