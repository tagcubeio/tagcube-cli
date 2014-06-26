import os
import yaml


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