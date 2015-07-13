from urlparse import urlparse
from tagcube_cli.logger import cli_logger


def do_batch_scan(client, cmd_args):
    if not client.test_auth_credentials():
        raise ValueError('Invalid TagCube REST API credentials.')

    cli_logger.debug('Authentication credentials are valid')

    for scan in create_scans(cmd_args.urls_file):
        scan_resource = client.quick_scan(scan.get_root_url(),
                                          email_notify=cmd_args.email_notify,
                                          scan_profile=cmd_args.scan_profile,
                                          path_list=scan.get_paths())

        # pylint: disable=E1101
        args = (scan_resource.id, scan.get_root_url())
        cli_logger.info('Launched scan #%s to %s' % args)
        # pylint: enable=E1101


def create_scans(urls_file):
    """
    This method is rather simple, it will group the urls to be scanner together
    based on (protocol, domain and port).

    :param urls_file: The filename with all the URLs
    :return: A list of scans to be run
    """
    cli_logger.debug('Starting to process batch input file')
    created_scans = []

    for line in urls_file:
        line = line.strip()

        if line.startswith('#'):
            continue

        if not line:
            continue

        try:
            protocol, domain, port, path = parse_url(line)
        except ValueError, ve:
            cli_logger.debug(str(ve))
            continue

        for scan in created_scans:
            if scan.matches(protocol, domain, port):
                scan.add_path(path)
                args = (path, scan.get_root_url())
                cli_logger.debug('Added %s to %s' % args)
                break
        else:
            scan = BatchScan(protocol, domain, port, path)
            created_scans.append(scan)
            cli_logger.debug('Added a new scan to %s' % scan.get_root_url())

    cli_logger.debug('Created a total of %s scans' % len(created_scans))
    return created_scans


def parse_url(url):
    """
    Parse a URL into the parts I need for processing:
        * protocol
        * domain
        * port
        * path

    :param url: A string
    :return: A tuple containing the above
    """
    split_url = url.split('/', 3)
    if len(split_url) == 3:
        # http://foo.com
        path = '/'
    elif len(split_url) == 4:
        path = '/' + split_url[3]
    else:
        raise ValueError('Invalid URL: %s' % url)

    try:
        parse_result = urlparse(url)
    except Exception:
        raise ValueError('Invalid URL: %s' % url)

    protocol = parse_result.scheme
    protocol = protocol.lower()
    if protocol not in ('http', 'https'):
        raise ValueError('Invalid URL protocol "%s"' % protocol)

    split_netloc = parse_result.netloc.split(':')
    domain = split_netloc[0]
    domain = domain.lower()

    if len(split_netloc) == 2:
        try:
            port = int(split_netloc[1])
        except:
            raise ValueError('Invalid port: "%s"' % split_netloc[1])
    elif protocol == 'https':
        port = 443
    elif protocol == 'http':
        port = 80
    else:
        raise ValueError('Invalid scheme: "%s"' % protocol)

    return protocol, domain, port, path


class BatchScan(object):
    def __init__(self, protocol, domain, port, path):
        self.protocol = protocol
        self.domain = domain
        self.port = port

        self.paths = set()
        self.paths.add(path)

    def get_root_url(self):
        return '%s://%s:%s/' % (self.protocol, self.domain, self.port)

    def matches(self, protocol, domain, port):
        return (self.protocol == protocol and
                self.domain == domain and
                self.port == port)

    def add_path(self, path):
        return self.paths.add(path)

    def get_paths(self):
        return list(self.paths)