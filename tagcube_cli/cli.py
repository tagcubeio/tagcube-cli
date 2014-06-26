import argparse
import logging

from tagcube_cli.utils import parse_config_file, get_config_from_env
from tagcube import TagCubeClient

DESCRIPTION = 'TagCube client - %s' % TagCubeClient.ROOT_URL
EPILOG = '''\
examples:\n

 * Run a scan to http://target.com/, notify the REST API username email address
   when it finishes

        tagcube-cli --target-url=http://target.com

 * Run a scan with a custom profile, enabling verbose mode and notifying a
   different email address when the scan finishes

        tagcube-cli --target-url=http://target.com --email-notify=other@example.com \\
                    --scan-profile=fast_scan -v

 * Provide TagCube's REST API credentials as command line arguments. Read the
   documentation to find how to provide REST API credentials using environment
   variables or the .tagcube file

        tagcube-cli --target-url=http://target.com  --tagcube-email=user@example.com \\
                    --tagcube-api-key=...

 * Verify that the configured credentials are working

        tagcube-cli --auth-test
'''


class TagCubeCLI(object):
    """
    The main class for the CLI:
        * Receives parsed command line arguments
        * Creates and configures a TagCubeClient instance
        * Launches a scan
    """

    def __init__(self, email, api_key, cmd_args):
        self.client = TagCubeClient(email, api_key)
        self.cmd_args = cmd_args

    @classmethod
    def from_cmd_args(cls, cmd_args):
        email, api_key = cls.get_credentials(cmd_args)
        return cls(email, api_key, cmd_args)

    def run(self):
        """
        This method handles the user's command line arguments, for example, if
        the user specified a path file we'll open it and read the contents.
        Finally it will run the scan using TagCubeClient.scan(...)
        """
        if not self.client.test_auth_credentials():
            raise ValueError('Invalid TagCube REST API credentials.')

        logging.debug('Authentication credentials are valid')

        raise NotImplementedError

    @staticmethod
    def parse_args(args=None):
        """
        :return: The result of applying arparse to sys.argv
        """
        parser = CustomArgParser(prog='tagcube-cli',
                                 description=DESCRIPTION,
                                 epilog=EPILOG,
                                 formatter_class=CustomHelpFormatter)

        parser.add_argument('--target-url',
                            required=False,
                            dest='target_url',
                            help='URL for web application security scan.'
                                 '(e.g. https://www.target.com/)')

        parser.add_argument('--email-notify',
                            required=False,
                            dest='email_notify',
                            help='Email address to notify when application'
                                 ' scan finishes')

        parser.add_argument('--auth-test',
                            required=False,
                            dest='auth_test',
                            action='store_true',
                            help='Test configured authentication credentials'
                                 ' and exit. No target URL nor email'
                                 ' notifications need to be configured to'
                                 ' verify the credentials.')

        parser.add_argument('--tagcube-email',
                            required=False,
                            dest='tagcube_email',
                            help='The email address to use when sending'
                                 ' requests to TagCube\'s REST API')

        parser.add_argument('--tagcube-api-key',
                            required=False,
                            dest='tagcube_api_key',
                            help='The API key to use when sending requests'
                                 ' to TagCube\'s REST API')

        parser.add_argument('--scan-profile',
                            required=False,
                            dest='scan_profile',
                            default='full_audit',
                            help='The web application scan profile to use.'
                                 ' A complete list of scan profiles can be'
                                 ' retrieved from the API or Web UI.')

        parser.add_argument('--path-file',
                            required=False,
                            dest='path_file',
                            type=argparse.FileType('r'),
                            help='A file specifying the URL paths (without the'
                                 ' domain name) which TagCube will use to'
                                 ' bootstrap the web crawler. The "/" path'
                                 ' is used when no --path-file parameter is'
                                 ' specified.')

        parser.add_argument('-v',
                            required=False,
                            dest='verbose',
                            action='store_true',
                            help='Enables verbose output')

        cmd_args = parser.parse_args(args)

        if len([x for x in (cmd_args.tagcube_api_key, cmd_args.tagcube_email) if x is not None]) == 1:
            parser.error('--tagcube-api-key and --tagcube-email must be given'
                         ' together')

        if cmd_args.auth_test:
            # When auth_test is specified, we'll just perform that action and
            # exit, so all the other parameters are ignored. We want to enforce
            # that action here
            if cmd_args.target_url is not None or\
            cmd_args.email_notify is not None:
                parser.error('--target-url and --email-notify should not be'
                             ' set when --auth-test is.')
        else:
            if cmd_args.target_url is None:
                parser.error('argument --target-url is required')

        level = logging.DEBUG if cmd_args.verbose else logging.INFO
        logging.basicConfig(format='%(message)s', level=level)

        return cmd_args

    @staticmethod
    def get_credentials(cmd_args):
        """
        :return: The email and api_key to use to connect to TagCube. This
                 function will try to get the credentials from:
                    * Command line arguments
                    * Environment variables
                    * Configuration file

                 It will return the first match, in the order specified above.
        """
        # Check the cmd args, return if we have something here
        cmd_credentials = cmd_args.tagcube_email, cmd_args.tagcube_api_key
        if cmd_credentials != (None, None):
            logging.debug('Using command line configured credentials')
            return cmd_credentials

        env_email, env_api_key = get_config_from_env()
        if env_email is not None:
            if env_api_key is not None:
                logging.debug('Using environment configured credentials')
                return env_email, env_api_key

        cfg_email, cfg_api_key = parse_config_file()
        if cfg_email is not None:
            if cfg_api_key is not None:
                logging.debug('Using .tagcube file configured credentials')
                return cfg_email, cfg_api_key

        raise ValueError('No credentials provided at: command line argument,'
                         ' configuration file or environment variables.')


class CustomArgParser(argparse.ArgumentParser):
    def format_help(self):
        """
        Overriding to call add_raw_text
        """
        formatter = self._get_formatter()

        # usage
        formatter.add_usage(self.usage, self._actions,
                            self._mutually_exclusive_groups)

        # description
        formatter.add_text(self.description)

        # positionals, optionals and user-defined groups
        for action_group in self._action_groups:
            formatter.start_section(action_group.title)
            formatter.add_text(action_group.description)
            formatter.add_arguments(action_group._group_actions)
            formatter.end_section()

        # epilog
        formatter.add_raw_text(self.epilog)

        # determine help from format above
        return formatter.format_help()


class CustomHelpFormatter(argparse.HelpFormatter):
    def add_raw_text(self, text):
        self._add_item(lambda x: x, [text])