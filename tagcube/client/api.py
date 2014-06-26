import requests
import logging
import json

from tagcube.utils.urlparsing import get_domain_from_url, get_port_from_url

CAN_NOT_SCAN_DOMAIN_ERROR = '''\
You can't scan the specified domain. This happens in the following cases:

 * The current plan only allows scans to verified domains => Verify your domain
 ownership using TagCube's web UI or the REST API.

 * The domain quota for your plan has been exceeded => Upgrade your plan to be
 able to scan more domains.

'''


class TagCubeClient(object):

    ROOT_URL = 'https://www.tagcube.io/'
    API_VERSION = '1.0'
    SELF_URL = '/users/~'

    def __init__(self, email, api_key):
        self.email = email
        self.api_key = api_key
        self.session = None
        self.configure_requests()

    def test_auth_credentials(self):
        """
        :return: True when the credentials are properly configured.
        """
        code, json = self.send_request(self.build_url(self.SELF_URL))
        return code == requests.codes.ok

    def quick_scan(self, target_url, email_notify=None,
                   scan_profile='full_audit', path_list=('/',)):
        """
        :param target_url: The target url e.g. https://www.tagcube.io/
        :param email_notify: The notification email e.g. user@example.com
        :param scan_profile: The name of the scan profile
        :param path_list: The list of paths to use in the crawling bootstrap

        The basic idea around this method is to provide users with a quick way
        to start a new scan. We perform these steps:

            * If the domain in the target_url is not created, we create a new
            domain resource for it.

            * We verify that the user's license can scan the target domain (new
            or already created manually by the user)

            * We'll notify about this scan via email, if no email_notify is
            specified we'll use the TagCube's user email for notification. If
            there is no email notification for this email, we'll create one.

            * The scan will be started using the scan_profile and path_list
            provided as parameter.

        Lots of bad things can trigger errors. All errors trigger exceptions.
        Some of the situations where you'll get errors are:

            * The user's license can't scan the provided domain

            * We failed to connect to the REST API

            * The specified scan_profile does not exist

        :return: The newly generated scan id
        """
        #
        # Scan profile handling
        #
        scan_profile_resource = self.get_scan_profile(scan_profile)
        if scan_profile_resource is None:
            msg = 'The specified scan profile "%s" does not exist'
            raise ValueError(msg % scan_profile)

        #
        # Domain resource handling
        #
        domain = get_domain_from_url(target_url)

        domain_resource = self.get_domain(domain)
        if domain_resource is None:
            domain_resource = self.domain_add(domain)

        if not self.can_scan(domain):
            raise ValueError(CAN_NOT_SCAN_DOMAIN_ERROR)

        #
        # Email notification handling
        #
        notif_email = self.email if email_notify is None else email_notify
        email_notification_resource = self.get_email_notification(notif_email)
        if email_notification_resource is None:
            email_notification_resource = self.email_notification_add(notif_email)

        #
        # Scan!
        #
        port = get_port_from_url(target_url)

        return self.low_level_scan(domain_resource, port, scan_profile_resource,
                                   path_list, [email_notification_resource])

    def low_level_scan(self, domain_resource, port, scan_profile_resource,
                       path_list, notification_resource_list):
        """
        Low level implementation of the scan launch which allows you to start
        a new scan when you already know the ids for the required resources.

        :param domain_resource: The domain resource to scan
        :param port: The TCP port to scan
        :param scan_profile_resource: The scan profile resource
        :param path_list: A list with the paths
        :param notification_resource_list: The notifications to use

        All the *_resource* parameters are obtained by calling the respective
        getters such as:
            - get_domain
            - get_email_notification
            - get_scan_profile

        :return: The newly generated scan id
        """
        raise NotImplementedError

    def get_scan_profile(self, scan_profile):
        """
        :return: The scan profile resource (as json), or None
        """
        raise NotImplementedError

    def get_email_notification(self, notif_email):
        """
        :return: The email notification resource for notif_email, or None
        """
        raise NotImplementedError

    def email_notification_add(self, notif_email):
        """
        :return: The id of the newly created email notification resource
        """
        raise NotImplementedError

    def can_scan(self, domain):
        """
        :return: True if the current user can scan the specified domain
        """
        raise NotImplementedError

    def get_domain(self, domain):
        """
        :param domain: The domain to query
        :return: The domain resource (as json), or None
        """
        raise NotImplementedError

    def domain_add(self, domain):
        """
        :param domain: The domain name to add as a new resource
        :return: The newly created domain id
        """
        raise NotImplementedError

    def configure_requests(self):
        # We disable the logging of the requests module to avoid some infinite
        # recursion errors that might appear.
        requests_log = logging.getLogger("requests")
        requests_log.setLevel(logging.CRITICAL)

        self.session = requests.Session()
        self.session.auth = (self.email, self.api_key)
        self.session.headers.update({'Content-Type': 'application/json'})

    def send_request(self, url, json_data=None, method='GET'):
        if method == 'GET':
            response = self.session.get(url)

        elif method == 'POST':
            data = json.dumps(json_data)
            response = self.session.post(url, data=data)

        else:
            raise ValueError('Invalid HTTP method: "%s"' % method)

        return response.status_code, response.json()

    def build_url(self, last_part):
        return '%s%s%s' % (self.ROOT_URL, self.API_VERSION, last_part)