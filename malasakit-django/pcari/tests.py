from django.test import TestCase

# TODO: remove once we know Travis sees this test
class SanityCheckTestCase(TestCase):  
    def testSanity(self):
        self.assertEquals(1, 1)
