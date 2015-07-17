from tagcube_cli.logger import cli_logger


def do_auth_test(client, cmd_args):
    """
    Handle the case where the user runs "tagcube auth"
    """
    current_user = client.get_current_user()
    if current_user is None:
        msg = 'Invalid TagCube REST API credentials for %s'
        raise ValueError(msg % client.email)

    email = current_user.get('email')
    msg = 'Successfully authenticated using %s\'s REST API key'
    cli_logger.info(msg % email)

