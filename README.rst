TagCube cli tool
================

Tool to launch web application security scans using TagCube's REST API, commonly
used in continuous delivery scripts.

.. image:: https://circleci.com/gh/andresriancho/tagcube-cli.png?circle-token=dc4aa96d817b9d41baf6778f2db9b3fe87d6b5e2
   :alt: Build Status
   :align: right
   :target: https://circleci.com/gh/andresriancho/tagcube-cli
   
Usage
=====

The easiest way to start a new scan is to call ``tagcube-cli`` with the domain
as parameter:

::

    $ tagcube-cli domain.com --email-notify=user@example.com
    Web application scan for "domain.com" successfully started at TagCube cloud.

This will create the new domain resource in TagCube's REST API and start a new
scan using these defaults:

    * Bootstrap paths: ``/``
    * Web application scan profile: ``full_audit``
    * No web application authentication credentials

When the scan has finished an email will be sent to ``user@example.com``.

**Important**: depending on TagCube's license quotas and privileges you might need to
use the REST API or Web application to create and verify the ownership of the
target domain before running the first scan against it.

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

Reporting bugs
==============

Report your issues and feature requests in `tagcube-cli's issue
tracker <https://github.com/andresriancho/tagcube-cli/issues>`_ and we'll
be more than glad to fix them.

Pull requests are more than welcome!

