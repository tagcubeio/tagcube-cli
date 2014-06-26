import urlparse


def get_domain_from_url(url):
    return urlparse.urlparse(url).netloc.split(':')[0]


def get_port_from_url(url):
    if url.startswith('http://'):
        default = '80'
    elif url.startswith('https://'):
        default = '443'
    else:
        default = '80'

    try:
        port = urlparse.urlparse(url).netloc.split(':')[1]
    except IndexError:
        return default
    else:
        return port