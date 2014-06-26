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


def path_file_to_list(path_file):
    """
    :return: A list with the paths which are stored in a text file in a line-by-
             line format. Validate each path using is_valid_path
    """
    paths = []

    for line_no, line in enumerate(path_file.readlines(), start=1):
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
            raise ValueError('%s Error found in line %s.' % (ve, line_no))

    return paths
