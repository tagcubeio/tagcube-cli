import unittest
import tempfile
import os

from tagcube_cli.utils import _parse_config_file_impl


CONFIG_FMT = '''\
credentials:
    email: %s
    api_key: %s
'''


class TestParseConfigFile(unittest.TestCase):
    def test_parse_config_ok(self):
        
        EMAIL = 'abc@def.com'
        API_TOKEN = 'ffe83b68-7b6f-4992-a0ee-a1cf57f8072f'
        
        fh = tempfile.NamedTemporaryFile('w', delete=False)
        fh.write(CONFIG_FMT % (EMAIL, API_TOKEN))
        fh.close()
        
        email, api_token = _parse_config_file_impl(fh.name)
        self.assertEqual(email, EMAIL)
        self.assertEqual(api_token, API_TOKEN)
        
        os.unlink(fh.name)

    def test_parse_config_not_exists(self):
        self.assertRaises(IOError, _parse_config_file_impl, '/foo/bar')

    def test_parse_config_invalid_format(self):
        fh = tempfile.NamedTemporaryFile('w', delete=False)
        fh.write('hello world!')
        
        email, api_token = _parse_config_file_impl(fh.name)
        self.assertEqual(email, None)
        self.assertEqual(api_token, None)
