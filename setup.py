#!/usr/bin/env python

from setuptools import setup, find_packages
from os.path import join, dirname

setup(
      name='tagcube-cli',

      version='0.1.2',
      license = 'GNU General Public License v2 (GPLv2)',
      platforms='Linux',
      
      description=('CLI to launch web application security scans using'
                   'TagCube\'s REST API '),
      long_description=file(join(dirname(__file__), 'README.rst')).read(),
      
      author='TagCube',
      author_email='support@tagcube.io',
      url='https://github.com/tagcubeio/tagcube-cli/',
      
      packages=find_packages(),
      include_package_data=True,
      install_requires=['requests>=2.3.0', 'PyYAML>=3.11'],

      entry_points={
          'console_scripts':
              ['tagcube-cli = tagcube_cli.main:main']
      },

      # https://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Topic :: System :: Monitoring'
        ],
      
       # In order to run this command: python setup.py test
       test_suite="nose.collector",
       tests_require="nose",
     )
