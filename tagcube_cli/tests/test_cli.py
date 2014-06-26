import unittest

from mock import patch

from tagcube_cli.cli import TagCubeCLI


class TestTagCubeCLI(unittest.TestCase):

    SIMPLE_ARGS = ['target.com', '--email-notify=a@b.com']

    def test_user_pass_environment(self):
        with patch.dict('os.environ', {'TAGCUBE_EMAIL': 'x@y.com',
                                       'TAGCUBE_API_KEY': 'w'}):

            parsed_args = TagCubeCLI.parse_args(self.SIMPLE_ARGS)
            tagcube_cli = TagCubeCLI.from_cmd_args(parsed_args)
            self.assertEqual(tagcube_cli.client.email, 'x@y.com')
            self.assertEqual(tagcube_cli.client.api_key, 'w')

    def test_user_pass_none(self):
        parsed_args = TagCubeCLI.parse_args(self.SIMPLE_ARGS)
        self.assertRaises(ValueError, TagCubeCLI.from_cmd_args, parsed_args)

    def test_user_pass_command_line_with_creds(self):
        args = self.SIMPLE_ARGS + ['--tagcube-email=x@y.com', '--tagcube-api-key=w']

        parsed_args = TagCubeCLI.parse_args(args)
        tagcube_cli = TagCubeCLI.from_cmd_args(parsed_args)
        self.assertEqual(tagcube_cli.client.email, 'x@y.com')
        self.assertEqual(tagcube_cli.client.api_key, 'w')
