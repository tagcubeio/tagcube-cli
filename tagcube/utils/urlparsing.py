import urlparse


def get_domain_from_url(url):
    return urlparse.urlparse(url).netloc.split(':')[0]


def get_port_from_url(url):
    if url.lower().startswith('http://'):
        default = '80'
    elif url.lower().startswith('https://'):
        default = '443'
    else:
        default = '80'

    try:
        port = urlparse.urlparse(url).netloc.split(':')[1]
    except IndexError:
        return default
    else:
        return port


def use_ssl(url):
    return url.lower().startswith('https://')