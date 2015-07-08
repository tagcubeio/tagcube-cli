from tagcube_cli.logger import cli_logger


def do_auth_test(client, cmd_args):
    """
    Handle the case where the user runs "tagcube auth"
    """
    if not client.test_auth_credentials():
        raise ValueError('Invalid TagCube REST API credentials.')

    cli_logger.info('TagCube credentials are valid')

