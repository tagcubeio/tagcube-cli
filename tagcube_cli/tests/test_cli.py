import unittest
import tempfile
import shutil
import os

from mock import patch, call

from tagcube_cli.cli import TagCubeCLI


class TestTagCubeCLI(unittest.TestCase):

    SIMPLE_ARGS = ['scan', '--root-url', 'http://target.com']
    TAGCUBE_FILE = '.tagcube'
    TAGCUBE_FILE_BACKUP = '.tagcube-unittest-backup'

    def setUp(self):
        super(TestTagCubeCLI, self).setUp()

        if os.path.exists(self.TAGCUBE_FILE):
            shutil.move(self.TAGCUBE_FILE, self.TAGCUBE_FILE_BACKUP)

    def tearDown(self):
        super(TestTagCubeCLI, self).tearDown()

        if os.path.exists(self.TAGCUBE_FILE_BACKUP):
            shutil.move(self.TAGCUBE_FILE_BACKUP, self.TAGCUBE_FILE)

    def test_user_pass_environment(self):
        with patch.dict('os.environ', {'TAGCUBE_EMAIL': 'x@y.com',
                                       'TAGCUBE_API_KEY': 'w'}):

            parsed_args = TagCubeCLI.parse_args(self.SIMPLE_ARGS)
            email, api_key = TagCubeCLI.get_credentials(parsed_args)
            self.assertEqual(email, 'x@y.com')
            self.assertEqual(api_key, 'w')

    def test_user_pass_none(self):
        parsed_args = TagCubeCLI.parse_args(self.SIMPLE_ARGS)
        self.assertRaises(ValueError, TagCubeCLI.get_credentials, parsed_args)

    def test_user_pass_command_line_with_creds(self):
        args = self.SIMPLE_ARGS + ['--email=x@y.com', '--key=w']

        parsed_args = TagCubeCLI.parse_args(args)
        email, api_key = TagCubeCLI.get_credentials(parsed_args)
        self.assertEqual(email, 'x@y.com')
        self.assertEqual(api_key, 'w')

    def test_parse_path_file_ok(self):
        path_file = '/foo\n/bar'

        fh = tempfile.NamedTemporaryFile('w', delete=False)
        fh.write(path_file)
        fh.close()

        args = self.SIMPLE_ARGS + ['--path-file=%s' % fh.name]
        parsed_args = TagCubeCLI.parse_args(args)
        self.assertEqual(parsed_args.path_file, ['/foo', '/bar'])

    def test_parse_path_file_incorrect_format(self):
        path_file = 'bar'

        fh = tempfile.NamedTemporaryFile('w', delete=False)
        fh.write(path_file)
        fh.close()

        args = self.SIMPLE_ARGS + ['--path-file=%s' % fh.name]

        with patch('argparse._sys.exit') as exit_mock,\
        patch('argparse._sys.stderr') as stderr_mock:
            self.assertRaises(TypeError, TagCubeCLI.parse_args, args)

            self.assertEqual(exit_mock.call_args_list, [call(2)])
            self.assertEqual(stderr_mock.call_args_list, [])