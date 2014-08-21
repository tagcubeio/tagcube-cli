#!/bin/bash

set -e

echo "[server-login]" > ~/.pypirc
echo "username:" $PYPI_USER >> ~/.pypirc
echo "password:" $PYPI_PASSWORD >> ~/.pypirc

PACKAGE_URL='https://pypi.python.org/packages/source/t/tagcube-cli/'

packages=`curl -f -s -S -k $PACKAGE_URL`
tagcube_version=`python -c 'from tagcube import __VERSION__;print __VERSION__,'`
current_package="tagcube-cli-$tagcube_version.tar.gz"

if [[ $packages == *$current_package* ]]
then
    echo "Current package version is already at PyPi. If your intention was to"
    echo "release a new version, you'll have to increase the version number."
else
    echo "Uploading $tagcube_version version to PyPi"
    python setup.py sdist upload
fi