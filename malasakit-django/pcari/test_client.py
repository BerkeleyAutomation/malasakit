import logging

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.shortcuts import reverse
from selenium.webdriver import Chrome, ChromeOptions, Firefox
from selenium.webdriver.common.keys import Keys

from pcari.models import QuantitativeQuestion, QualitativeQuestion

logging.disable(logging.CRITICAL)


def use_drivers(*test_drivers):
    def decorator(test_method):
        def test_method_wrapper(self):
            for driver in test_drivers:
                instance = driver()
                instance.start()
                test_method(self, instance)
                instance.stop()
        return test_method_wrapper
    return decorator


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


def make_test_web_drivers():
    chrome_options = ChromeOptions()
    chrome_options.add_argument('headless')
    return [
        make_test_web_driver(Chrome, desired_capabilities=chrome_options.to_capabilities()),
    ]

WEB_DRIVERS = make_test_web_drivers()


class NavigationTestCase(StaticLiveServerTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.questions = [QuantitativeQuestion.objects.create() for _ in range(8)]

    @use_drivers(*WEB_DRIVERS)
    def test_complete_walkthrough(self, driver):
        driver.get(self.live_server_url + reverse('pcari:landing'))
        html = driver.find_element_by_tag_name('html')
        driver.find_element_by_id('next').click()
        for _ in range(len(self.questions)):
            self.assertIn(reverse('pcari:quantitative-questions'), driver.current_url)
            driver.find_element_by_id('submit').click()
        self.assertIn(reverse('pcari:rate-comments'), driver.current_url)
