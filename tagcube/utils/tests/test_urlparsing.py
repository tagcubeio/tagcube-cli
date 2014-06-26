import unittest

from tagcube.utils.urlparsing import get_port_from_url, get_domain_from_url


class TestURLParsing(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(get_port_from_url('https://www.tagcube.io/'), '443')
        self.assertEqual(get_domain_from_url('https://www.tagcube.io/'),
                         'www.tagcube.io')

    def test_port_specified(self):
        self.assertEqual(get_port_from_url('https://www.tagcube.io:22/'), '22')
        self.assertEqual(get_domain_from_url('https://www.tagcube.io/'),
                         'www.tagcube.io')
