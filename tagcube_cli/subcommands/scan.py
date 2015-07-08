from tagcube_cli.logger import cli_logger


def do_scan_start(client, cmd_args):
    if not client.test_auth_credentials():
        raise ValueError('Invalid TagCube REST API credentials.')

    cli_logger.debug('Authentication credentials are valid')
    cli_logger.debug('Starting web application scan')

    scan_resource = client.quick_scan(cmd_args.root_url,
                                      email_notify=cmd_args.email_notify,
                                      scan_profile=cmd_args.scan_profile,
                                      path_list=cmd_args.path_file)

    # pylint: disable=E1101
    cli_logger.info('Launched scan with id #%s' % scan_resource.id)
    # pylint: enable=E1101

