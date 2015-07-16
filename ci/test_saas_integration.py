import unittest
import os
import subprocess
import re
import time
import pprint

from tagcube.client.api import TagCubeClient


class TestTagCubeSaaSIntegration(unittest.TestCase):

    TARGET_URL = 'http://www.fogfu.com/'

    STAGING_ROOT_URL = os.environ.get('STAGING_ROOT_URL')

    BRANCH = os.environ.get('CIRCLE_BRANCH', 'DEVELOP').upper()
    TAGCUBE_API_KEY = os.environ.get('TAGCUBE_API_KEY_%s' % BRANCH)
    TAGCUBE_EMAIL = os.environ.get('TAGCUBE_EMAIL_%s' % BRANCH)

    TAGCUBE_SCAN_CMD_FMT = 'tagcube scan --scan-profile=fast_scan -v --root-url %s'
    TAGCUBE_AUTH_CMD = 'tagcube auth -v'
    TAGCUBE_VERSION_CMD = 'tagcube version'

    def setUp(self):
        self.assertIsNotNone(self.STAGING_ROOT_URL)
        self.assertIsNotNone(self.TAGCUBE_API_KEY)
        self.assertIsNotNone(self.TAGCUBE_EMAIL)

        # Translate TAGCUBE_EMAIL_DEVELOP into TAGCUBE_EMAIL
        os.environ['TAGCUBE_EMAIL'] = self.TAGCUBE_EMAIL
        os.environ['TAGCUBE_API_KEY'] = self.TAGCUBE_API_KEY

    def test_integration(self):
        """
        * Set the ROOT_URL to launch the scan in the right environment

        * Launch a scan against TARGET_URL

        * Monitor the scan using Tagcube's REST API to make sure the scan finds
        at least two vulnerabilities
        """
        self.set_root_url()
        self.verify_credentials()
        self.get_version()
        scan_id = self.start_scan()
        self.monitor_scan(scan_id)

    def set_root_url(self):
        """
        If the CIRCLE_BRANCH is set to 'develop' or not-set we want to run our
        tests against the STAGING_ROOT_URL (test staging). Else just use the
        default in tagcube-cli.

        :return: None
        """
        if os.environ.get('CIRCLE_BRANCH', None) in ('develop', None):
            os.environ['ROOT_URL'] = self.STAGING_ROOT_URL

    def verify_credentials(self):
        print(self.TAGCUBE_AUTH_CMD)

        try:
            print(subprocess.check_output(self.TAGCUBE_AUTH_CMD,
                                          stderr=subprocess.STDOUT,
                                          shell=True))
        except subprocess.CalledProcessError, cpe:
            msg = '"%s" failed. The output was:\n%s'
            self.assertTrue(False, msg % (self.TAGCUBE_AUTH_CMD, cpe.output))

    def get_version(self):
        print(self.TAGCUBE_VERSION_CMD)

        try:
            print(subprocess.check_output(self.TAGCUBE_VERSION_CMD,
                                          stderr=subprocess.STDOUT,
                                          shell=True))
        except subprocess.CalledProcessError, cpe:
            msg = '"%s" failed. The output was:\n%s'
            self.assertTrue(False, msg % (self.TAGCUBE_VERSION_CMD, cpe.output))

    def start_scan(self):
        """
        Start a scan against TARGET_URL using the credentials configured in
        the environment variables

        Starting a scan should return quickly and the exit code must be zero

        :return: The scan id as a string
        """
        command = self.TAGCUBE_SCAN_CMD_FMT % self.TARGET_URL
        print(command)

        try:
            output = subprocess.check_output(command, shell=True,
                                             stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError, cpe:
            msg = '"%s" failed. The output was:\n%s'
            self.assertTrue(False, msg % (command, cpe.output))
        else:
            print(output)

            self.assertIn('Launched scan with id #', output)
            scan_id = re.search('Launched scan with id #(.*)', output).group(1)
            return scan_id.strip()

    def monitor_scan(self, scan_id):
        """
        Monitors the scan with id `scan_id` until it has two vulnerabilities
        (success) or ten minutes go by (fail).

        :param scan_id: The scan_id to monitor
        :return: None
        """
        WAIT_TIME_SEC = 15
        MAX_SCAN_TIME_SEC = 10 * 60

        client = TagCubeClient(self.TAGCUBE_EMAIL, self.TAGCUBE_API_KEY,
                               verbose=True)

        for _ in xrange(MAX_SCAN_TIME_SEC/WAIT_TIME_SEC):
            scan_resource = client.get_scan(scan_id)

            if len(scan_resource['vulnerabilities_href']) >= 2:
                print('Success! At least two vulnerabilities found')
                return

            time.sleep(WAIT_TIME_SEC)

        msg = 'Scan seems to have failed. The latest scan resource is: %s'
        self.assertTrue(False, msg % pprint.pformat(scan_resource, indent=4))