import pytest
from unittest import TestCase


@pytest.mark.usefixtures("test_app")
class BaseSanicTestCase(TestCase):
    document = None

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        pass
