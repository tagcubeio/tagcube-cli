import sys

from tagcube_cli.cli import TagCubeCLI


def main():
    """
    Project's main method which will parse the command line arguments, run a
    scan using the TagCubeClient and exit.
    """
    cmd_args = TagCubeCLI.parse_args()

    try:
        tagcube_cli = TagCubeCLI.from_cmd_args(cmd_args)
    except ValueError, ve:
        # We get here when there are no credentials configured
        print '%s' % ve
        sys.exit(1)

    try:
        sys.exit(tagcube_cli.run())
    except ValueError, ve:
        # We get here when the configured credentials had some issue (invalid)
        # or there was some error (such as invalid profile name) with the params
        print '%s' % ve
        sys.exit(2)


if __name__ == '__main__':
    main()


