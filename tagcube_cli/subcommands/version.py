from tagcube import __VERSION__


def do_version(*args):
    """
    Handle the case where the user runs "tagcube version"
    """
    print('TagCube CLI version %s' % __VERSION__)


