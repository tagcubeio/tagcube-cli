import argparse
import logging

from requests.exceptions import ConnectionError

from tagcube.client.api import TagCubeClient
from tagcube.utils.exceptions import TagCubeAPIException
from tagcube_cli.logger import cli_logger
from tagcube_cli.subcommands.auth import do_auth_test
from tagcube_cli.subcommands.scan import do_scan_start
from tagcube_cli.subcommands.batch import do_batch_scan
from tagcube_cli.utils import (parse_config_file, get_config_from_env,
                               argparse_url_type, argparse_path_list_type,
                               argparse_email_type)


DESCRIPTION = 'TagCube client - %s' % TagCubeClient.DEFAULT_ROOT_URL
EPILOG = 'More information and usage examples at https://tagcube.io/docs/cli/'

NO_CREDENTIALS_ERROR = '''
No credentials provided. Please use one of these methods to configure them:

    * --tagcube-email and --tagcube-api-key command line arguments

    * TAGCUBE_EMAIL and TAGCUBE_API_KEY environment variables

    * A '.tagcube' YAML file

More information at:
    https://www.tagcube.io/docs/cli/'''


class TagCubeCLI(object):
    """
    The main class for the CLI:
        * Receives parsed command line arguments
        * Creates and configures a TagCubeClient instance
        * Launches a scan
    """
    def __init__(self, email, api_key, cmd_args):
        self.client = TagCubeClient(email, api_key, verbose=cmd_args.verbose)
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

        :return: The exit code for our process
        """
        subcommands = {'auth': do_auth_test,
                       'scan': do_scan_start,
                       'batch': do_batch_scan}

        try:
            subcommands.get(self.cmd_args.subcommand)(self.client,
                                                      self.cmd_args)

        except ConnectionError, ce:
            msg = 'Failed to connect to TagCube REST API: "%s"'
            cli_logger.error(msg % ce)
            return 3

        except TagCubeAPIException, tae:
            cli_logger.error('%s' % tae)
            return 4

        return 0

    @staticmethod
    def parse_args(args=None):
        """
        :return: The result of applying argparse to sys.argv
        """
        #
        #   The main parser
        #
        parser = argparse.ArgumentParser(prog='tagcube',
                                         description=DESCRIPTION,
                                         epilog=EPILOG)

        #
        #   Parser for the common arguments
        #
        common_parser = argparse.ArgumentParser(add_help=False)

        common_parser.add_argument('--email',
                                   required=False,
                                   dest='email',
                                   type=argparse_email_type,
                                   help='The email address (user) to use when'
                                        ' sending requests to TagCube\'s REST'
                                        ' API')

        common_parser.add_argument('--key',
                                   required=False,
                                   dest='key',
                                   help='The API key to authenticate with'
                                        ' TagCube\'s REST API')

        common_parser.add_argument('-v',
                                   required=False,
                                   dest='verbose',
                                   action='store_true',
                                   help='Enables verbose output')

        #
        #   Parser for common scan arguments
        #
        scan_common = argparse.ArgumentParser(add_help=False)

        scan_common.add_argument('--scan-profile',
                                 required=False,
                                 dest='scan_profile',
                                 default='full_audit',
                                 help='The web application scan profile to use.'
                                      ' A complete list of scan profiles can be'
                                      ' retrieved from the API or Web UI.')

        scan_common.add_argument('--email-notify',
                                 required=False,
                                 dest='email_notify',
                                 type=argparse_email_type,
                                 help='Email address to notify when application'
                                      ' scan finishes')

        #
        #   Handle subcommands
        #
        subparsers = parser.add_subparsers(help='TagCube sub-commands',
                                           dest='subcommand')

        #
        #   Scan
        #
        scan_parser = subparsers.add_parser('scan',
                                            help='Web application security'
                                                 ' scan using TagCube',
                                            parents=[common_parser,
                                                     scan_common])

        scan_parser.add_argument('--root-url',
                                 required=True,
                                 dest='root_url',
                                 type=argparse_url_type,
                                 help='Root URL for web application security'
                                      ' scan (e.g. https://www.target.com/)')

        scan_parser.add_argument('--path-file',
                                 required=False,
                                 dest='path_file',
                                 default=['/'],
                                 type=argparse_path_list_type,
                                 help='A file specifying the URL paths (without'
                                      ' the domain name) which TagCube will use'
                                      ' to bootstrap the web crawler. The "/"'
                                      ' path is used when no'
                                      ' --path-file parameter is specified.')

        #
        #   Auth test subcommand
        #
        _help = ('Test configured authentication credentials and exit. No'
                 ' target URL nor email notifications need to be configured'
                 ' to verify the credentials.')
        auth_parser = subparsers.add_parser('auth',
                                            help=_help,
                                            parents=[common_parser])

        #
        #   Batch scan subcommand
        #
        _help = ('Scan multiple domains and URLs in one command, one scan will'
                 ' be started for each unique protocol-domain-port tuple, the'
                 ' URLs paths are processed and sent in the scan configuration')
        batch_parser = subparsers.add_parser('batch',
                                             help=_help,
                                             parents=[common_parser,
                                                      scan_common])

        batch_parser.add_argument('--urls-file',
                                  required=True,
                                  dest='urls_file',
                                  type=argparse.FileType('r'),
                                  help='Text file containing one URL per line')

        cmd_args = parser.parse_args(args)

        handlers = {'scan': TagCubeCLI.handle_scan_args,
                    'auth': TagCubeCLI.handle_auth_args,
                    'batch': TagCubeCLI.handle_batch_args}

        handler = handlers.get(cmd_args.subcommand)
        return handler(parser, cmd_args)

    @staticmethod
    def handle_global_args(parser, cmd_args):
        #
        #   Global/Parent extra argument parsing steps
        #
        together = (cmd_args.key, cmd_args.email)
        if len([x for x in together if x is not None]) == 1:
            parser.error('--key and --email must be used together')

        #   Enable debugging if required by the user
        level = logging.DEBUG if cmd_args.verbose else logging.INFO
        cli_logger.setLevel(level=level)

        ch = logging.StreamHandler()
        ch.setLevel(level)

        formatter = logging.Formatter('%(message)s')
        ch.setFormatter(formatter)
        cli_logger.addHandler(ch)

        return cmd_args

    @staticmethod
    def handle_auth_args(parser, cmd_args):
        TagCubeCLI.handle_global_args(parser, cmd_args)
        return cmd_args

    @staticmethod
    def handle_batch_args(parser, cmd_args):
        TagCubeCLI.handle_global_args(parser, cmd_args)
        return cmd_args

    @staticmethod
    def handle_scan_args(parser, cmd_args):
        TagCubeCLI.handle_global_args(parser, cmd_args)
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
        cmd_credentials = cmd_args.email, cmd_args.key
        if cmd_credentials != (None, None):
            cli_logger.debug('Using command line configured credentials')
            return cmd_credentials

        env_email, env_api_key = get_config_from_env()
        if env_email is not None:
            if env_api_key is not None:
                cli_logger.debug('Using environment configured credentials')
                return env_email, env_api_key

        cfg_email, cfg_api_key = parse_config_file()
        if cfg_email is not None:
            if cfg_api_key is not None:
                cli_logger.debug('Using .tagcube file configured credentials')
                return cfg_email, cfg_api_key

        raise ValueError(NO_CREDENTIALS_ERROR)
