import os
import yaml
import argparse


def parse_config_file():
    """
    Find the .tagcube config file in the current directory, or in the
    user's home and parse it. The one in the current directory has precedence.
    
    :return: A tuple with:
                - email
                - api_token
    """
    for filename in ('.tagcube', os.path.expanduser('~/.tagcube')):
        if os.path.exists(filename):
            email, api_key = _parse_config_file_impl(filename)
            if email is not None and api_key is not None:
                return email, api_key
    else:
        return None, None


def _parse_config_file_impl(filename):
    """
    Format for the file is:
    
         credentials:
             email: ...
             api_token: ...
    
    :param filename: The filename to parse
    :return: A tuple with:
                - email
                - api_token
    """
    try:
        doc = yaml.load(file(filename).read())
        
        email = doc["credentials"]["email"]
        api_key = doc["credentials"]["api_key"]
        
        return email, api_key
    except TypeError:
        msg = 'Invalid .tagcube configuration file'
        print(msg)

    except yaml.scanner.ScannerError, e:
        msg = 'Invalid .tagcube configuration file format: "%s" at line %s'
        print(msg % (e.problem, e.problem_mark.line))

    return None, None


def get_config_from_env():
    return (os.environ.get('TAGCUBE_EMAIL', None),
            os.environ.get('TAGCUBE_API_KEY', None))


def is_valid_email(email):
    """
    Very trivial check to verify that the user provided parameter is an email
    """
    return '@' in email and '.' in email


def is_valid_path(path):
    """
    :return: True if the path is valid, else raise a ValueError with the
             specific error
    """
    if not path.startswith('/'):
        msg = 'Invalid path "%s". Paths need to start with "/".'
        raise ValueError(msg % path[:40])

    for c in ' \t':
        if c in path:
            msg = 'Invalid character "%s" found in path. Paths need to be' \
                  ' URL-encoded.'
            raise ValueError(msg % c)

    return True


def argparse_email_type(email):
    if not is_valid_email(email):
        msg = '%s is not a valid email address.'
        raise argparse.ArgumentTypeError(msg % email)

    return email


def argparse_url_type(url):
    if url.startswith('http://'):
        return url

    if url.startswith('https://'):
        return url

    msg = '%s is not a valid URL.'
    raise argparse.ArgumentTypeError(msg % url)


def argparse_path_list_type(path_file):
    if not os.path.exists(path_file):
        msg = 'The provided --path-file does not exist'
        raise argparse.ArgumentTypeError(msg)

    try:
        file(path_file)
    except:
        msg = 'The provided --path-file can not be read'
        raise argparse.ArgumentTypeError(msg)

    try:
        return path_file_to_list(path_file)
    except ValueError, ve:
        raise argparse.ArgumentTypeError(str(ve))


def path_file_to_list(path_file):
    """
    :return: A list with the paths which are stored in a text file in a line-by-
             line format. Validate each path using is_valid_path
    """
    paths = []
    path_file_fd = file(path_file)

    for line_no, line in enumerate(path_file_fd.readlines(), start=1):
        line = line.strip()

        if not line:
            # Blank line support
            continue

        if line.startswith('#'):
            # Comment support
            continue

        try:
            is_valid_path(line)
            paths.append(line)
        except ValueError, ve:
            args = (ve, path_file, line_no)
            raise ValueError('%s error found in %s:%s.' % args)

    return paths
