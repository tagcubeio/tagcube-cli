TagCube's CLI tool
==================

Launch web application security scans using `TagCube's REST API <https://www.tagcube.io>`_,
commonly used in continuous delivery scripts.

.. image:: https://circleci.com/gh/tagcubeio/tagcube-cli.png?circle-token=5317e457dceef210130d20e0452eff7abf1d195b
   :alt: Build Status
   :align: right
   :target: https://circleci.com/gh/tagcubeio/tagcube-cli
   
Usage
=====

The easiest way to start a new scan is to call ``tagcube-cli`` with the target
URL as parameter:

::

    $ export TAGCUBE_EMAIL=user@example.com
    $ export TAGCUBE_API_KEY=`cat key.txt`
    $ tagcube-cli http://domain.com
    Web application scan for "http://domain.com/" successfully started at TagCube cloud.

This will create the new domain resource in TagCube's REST API and start a new
scan using these defaults:

- Bootstrap paths: ``/``
- Web application scan profile: ``full_audit``

When the scan has finished an email will be sent to the user's email address.

**Important**: depending on TagCube's license quotas and privileges you might need to
use the REST API or Web application to *create and verify the ownership of the
target domain* before running the first scan against it.

Advanced usage
==============

Run a scan to ``http://target.com/``, notify the REST API username email address
when it finishes

::

    $ tagcube-cli http://target.com


Run a scan with a custom profile, enabling verbose mode and notifying a
different email address when the scan finishes

::

    $ tagcube-cli http://target.com --email-notify=other@example.com \
                  --scan-profile=fast_scan -v

Provide TagCube's REST API credentials as command line arguments. Read the
documentation to find how to provide REST API credentials using environment
variables or the .tagcube file

::

    $ tagcube-cli http://target.com  --tagcube-email=user@example.com \
                  --tagcube-api-key=...

Verify that the configured credentials are working

::

    $ tagcube-cli --auth-test


Configuration file
==================

It is always a good idea to avoid hardcoded credentials in source code and deploy
scripts. This tool can get the credentials from a YAML file in the current directory
or the user's home. The filename should be named ``.tagcube`` and have the following
format:

::

    credentials:
        email: ...
        api_key: ...

Once the file is in place, the tool can be run:

::

    $ tagcube-cli --auth-test
    Successfully authenticated against TagCube's API.
    $


Configuration through environment variables
===========================================

Another way to provide ``tagcube-cli`` with the REST API credentials is to set
the ``TAGCUBE_EMAIL`` and ``TAGCUBE_API_KEY`` environment variables. These are
convenient to avoid hard-coding credentials in scripts or source code.

Integration with continuous delivery
====================================

Adding security to your continuous delivery process is trivial using TagCube,
we recommend adding these two lines after the code is pushed to the servers:

::

    pip install --upgrade tagcube-cli
    tagcube-cli http://target.com

While in most cases its recommend to be specific about the version of any
external package installed using ``pip``, we recommend a more relaxed installation
process for ``tagcube-cli`` which allows us to frequently push upgrades to our
customers.

More info
=========

A more detailed documentation which includes tutorials and example usages can
be found at `TagCube's site <https://www.tagcube.io/docs/cli/>`_

Reporting bugs
==============

Report your issues and feature requests in `tagcube-cli's issue
tracker <https://github.com/tagcubeio/tagcube-cli/issues>`_ and we'll
be more than glad to fix them.

Pull requests are more than welcome!

