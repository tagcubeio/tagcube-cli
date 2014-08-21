import os
import requests
import logging
import json
import urllib

# These two lines enable debugging at httplib level
# (requests->urllib3->http.client) You will see the REQUEST, including HEADERS
# and DATA, and RESPONSE with HEADERS but without DATA.
# The only thing missing will be the response.body which is not logged.
try:
    import http.client as http_client
except ImportError:
    # Python 2
    import httplib as http_client


from tagcube import __VERSION__
from tagcube.utils.exceptions import TagCubeAPIException, IncorrectAPICredentials
from tagcube.utils.resource import Resource
from tagcube.utils.result_handlers import (ONE_RESULT, LATEST_RESULT,
                                           RESULT_HANDLERS)
from tagcube.utils.urlparsing import (get_domain_from_url, use_ssl,
                                      get_port_from_url)

api_logger = logging.getLogger(__name__)

CAN_NOT_SCAN_DOMAIN_ERROR = '''\
You can't scan the specified domain. This happens in the following cases:

 * The current plan only allows scans to verified domains => Verify your domain
 ownership using TagCube's web UI or the REST API.

 * The domain quota for your plan has been exceeded => Upgrade your plan to be
 able to scan more domains.

'''


class TagCubeClient(object):

    DEFAULT_ROOT_URL = 'https://api.tagcube.io/'

    API_VERSION = '1.0'

    SELF_URL = '/users/~'
    DOMAINS = '/domains/'
    SCANS = '/scans/'
    VERIFICATIONS = '/verifications/'
    SCAN_PROFILES = '/profiles/'

    DESCRIPTION = 'Created by TagCube REST API client'

    def __init__(self, email, api_key, verbose=False):
        self.email = email
        self.api_key = api_key
        self.session = None

        self.root_url = os.environ.get('ROOT_URL', None) or self.DEFAULT_ROOT_URL

        self.set_verbose(verbose)
        self.configure_requests()

    def test_auth_credentials(self):
        """
        :return: True when the credentials are properly configured.
        """
        try:
            code, _ = self.send_request(self.build_full_url(self.SELF_URL))
        except IncorrectAPICredentials:
            return False
        else:
            return code == 200

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
        # Domain verification handling
        #
        domain = get_domain_from_url(target_url)
        port = get_port_from_url(target_url)
        is_ssl = use_ssl(target_url)

        # First, is there a domain resource to verify?
        domain_resource = self.get_domain(domain)
        if domain_resource is None:
            domain_resource = self.domain_add(domain)

        verification_resource = self.get_latest_verification(domain_resource.id,
                                                             port, is_ssl)

        if verification_resource is None:
            # This seems to be the first scan to this domain, we'll have to
            # verify the client's ownership.
            #
            # Depending on the user's configuration, license, etc. this can
            # succeed or fail
            verification_resource = self.verification_add(domain_resource.id,
                                                          port, is_ssl)

            if not self.can_scan(verification_resource):
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
        return self.low_level_scan(verification_resource, scan_profile_resource,
                                   path_list, [email_notification_resource])

    def low_level_scan(self, verification_resource, scan_profile_resource,
                       path_list, notification_resource_list):
        """
        Low level implementation of the scan launch which allows you to start
        a new scan when you already know the ids for the required resources.

        :param verification_resource: The verification associated with the
                                      domain resource to scan
        :param scan_profile_resource: The scan profile resource
        :param path_list: A list with the paths
        :param notification_resource_list: The notifications to use

        All the *_resource* parameters are obtained by calling the respective
        getters such as:
            - get_email_notification
            - get_scan_profile

        And are expected to be of Resource type

        This method's last step is to send a POST request to /1.0/scans/ using
        a post-data similar to:

            {"verification_href": "/1.0/verifications/6",
             "profile_href": "/1.0/profiles/2",
             "start_time": "now",
             "email_notifications_href": [],
             "path_list": ["/"]}'

        :return: The newly generated scan id
        """
        data = {"verification_href": verification_resource.href,
                "profile_href": scan_profile_resource.href,
                "start_time": "now",
                "email_notifications_href": [n.href for n in notification_resource_list],
                "path_list": path_list}
        url = self.build_full_url('/scans/')
        return self.create_resource(url, data)

    def get_scan_profile(self, scan_profile):
        """
        :return: The scan profile resource (as Resource), or None
        """
        return self.filter_resource('profiles', 'name', scan_profile)

    def verification_add(self, domain_resource_id, port, is_ssl):
        """
        Sends a POST to /1.0/verifications/ using this post-data:

            {"domain_href": "/1.0/domains/2",
             "port":80,
             "ssl":false}

        :param domain_resource_id: The domain id to verify
        :param port: The TCP port
        :param is_ssl: Boolean indicating if we should use ssl

        :return: The newly created resource
        """
        data = {"domain_href": self.build_api_path('domains',
                                                   domain_resource_id),
                "port": port,
                "ssl": 'true' if is_ssl else 'false'}
        url = self.build_full_url(self.VERIFICATIONS)
        return self.create_resource(url, data)

    def get_latest_verification(self, domain_resource_id, port, is_ssl):
        """
        :return: A verification resource (as Resource), or None. If there is
                 more than one verification resource available it will return
                 the latest one (the one with the higher id attribute).
        """
        filter_dict = {'port': port,
                       'ssl': 'true' if is_ssl else 'false',
                       'domain_href': domain_resource_id}
        return self.multi_filter_resource('verifications', filter_dict,
                                          result_handler=LATEST_RESULT)

    def multi_filter_resource(self, resource_name, filter_dict,
                              result_handler=ONE_RESULT):
        url = self.build_full_url('/%s/?%s' % (resource_name,
                                               urllib.urlencode(filter_dict)))
        code, _json = self.send_request(url)

        if isinstance(_json, dict) and 'error' in _json:
            # Catch errors like this one:
            #
            # {"error": "Invalid resource lookup data provided
            #            (mismatched type)."}
            raise TagCubeAPIException(_json['error'])

        return RESULT_HANDLERS[result_handler](resource_name,
                                               filter_dict, _json)

    def filter_resource(self, resource_name, field_name, field_value,
                        result_handler=ONE_RESULT):
        """
        :return: The resource (as json), or None
        """
        return self.multi_filter_resource(resource_name,
                                          {field_name: field_value},
                                          result_handler=result_handler)

    def get_email_notification(self, notif_email):
        """
        :return: The email notification resource for notif_email, or None
        """
        return self.filter_resource('notifications/email', 'email', notif_email)

    def email_notification_add(self, notif_email, first_name='None',
                               last_name='None', description=DESCRIPTION):
        """
        Sends a POST to /1.0/notifications/email/ using this post-data:

            {"email": "andres.riancho@gmail.com",
             "first_name": "Andres",
             "last_name": "Riancho",
             "description": "Notification email"}

        :return: The id of the newly created email notification resource
        """
        data = {"email": notif_email,
                "first_name": first_name,
                "last_name": last_name,
                "description": description}
        url = self.build_full_url('/notifications/email/')
        return self.create_resource(url, data)

    def can_scan(self, verification_resource):
        """
        Failed verifications look like this:
            {
                "domain": "/1.0/domains/5",
                "href": "/1.0/verifications/2",
                "id": 2,
                "port": 80,
                "ssl": false,
                "success": false,
                "verification_message": "The HTTP response body does NOT
                                         contain the verification code."
            }

        Successful verifications look like this:
            {
                "domain": "/1.0/domains/2",
                "href": "/1.0/verifications/3",
                "id": 3,
                "port": 80,
                "ssl": false,
                "success": true,
                "verification_message": "Verification success"
            }

        :return: True if the current user can scan the specified domain
                 associated with the verification
        """
        return verification_resource.success

    def get_domain(self, domain):
        """
        :param domain: The domain to query
        :return: The domain resource (as json), or None
        """
        return self.filter_resource('domains', 'domain', domain)

    def domain_add(self, domain, description=DESCRIPTION):
        """
        Sends a POST to /1.0/domains/ using this post-data:

            {"domain": "www.fogfu.com",
             "description":"Added by tagcube-api"}

        :param domain: The domain name to add as a new resource
        :return: The newly created resource
        """
        data = {"domain": domain,
                "description": description}
        url = self.build_full_url(self.DOMAINS)
        return self.create_resource(url, data)

    def get_scan(self, scan_id):
        """
        :param scan_id: The scan ID as a string
        :return: A resource containing the scan information
        """
        url = self.build_full_url('%s%s' % (self.SCANS, scan_id))
        _, json_data = self.send_request(url)
        return Resource(json_data)

    def create_resource(self, url, data):
        """
        Shortcut for creating a new resource
        :return: The newly created resource as a Resource object
        """
        status_code, json_data = self.send_request(url, data, method='POST')

        if status_code != 201:
            msg = 'Expected 201 status code, got %s. Failed to create resource.'
            raise TagCubeAPIException(msg % status_code)

        try:
            return Resource(json_data)
        except KeyError:
            # Parse the error and raise an exception, errors look like:
            # {u'error': [u'The domain foo.com already exists.']}
            error_string = u' '.join(json_data['error'])
            raise TagCubeAPIException(error_string)

    def set_verbose(self, verbose):
        # Get level based on verbose boolean
        level = logging.DEBUG if verbose else logging.CRITICAL

        # Configure my own logger
        api_logger.setLevel(level=level)

        ch = logging.StreamHandler()
        ch.setLevel(level)

        formatter = logging.Formatter('%(message)s')
        ch.setFormatter(formatter)
        api_logger.addHandler(ch)

        # Configure the loggers for urllib3, requests and httplib
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(level)
        requests_log.propagate = True

        requests_log = logging.getLogger("requests")
        requests_log.setLevel(level)

        http_client.HTTPConnection.debuglevel = 1 if verbose else 0

    def configure_requests(self):
        self.session = requests.Session()
        self.session.auth = (self.email, self.api_key)

        headers = {'Content-Type': 'application/json',
                   'User-Agent': 'TagCubeClient %s' % __VERSION__}
        self.session.headers.update(headers)

    def handle_api_errors(self, status_code, json_data):
        """
        This method parses all the HTTP responses sent by the REST API and
        raises exceptions if required. Basically tries to find responses with
        this format:

            {
                'error': ['The domain foo.com already exists.']
            }

        Or this other:
            {
                "scans": {
                    "__all__": [
                        "Not a verified domain. You need to verify..."
                    ]
                }
            }

        And raise TagCubeAPIException with the correct message.

        :param status_code: The HTTP response code
        :param json_data: The HTTP response body decoded as JSON
        """
        error_list = []

        if status_code == 400:
            for main_error_key in json_data:
                for sub_error_key in json_data[main_error_key]:
                    error_list.extend(json_data[main_error_key][sub_error_key])

        elif 'error' in json_data and len(json_data) == 1 \
        and isinstance(json_data, dict) and isinstance(json_data['error'], list):
            error_list = json_data['error']

        # Only raise an exception if we had any errors
        if error_list:
            error_string = u' '.join(error_list)
            raise TagCubeAPIException(error_string)

    def send_request(self, url, json_data=None, method='GET'):
        if method == 'GET':
            response = self.session.get(url)

        elif method == 'POST':
            data = json.dumps(json_data)
            response = self.session.post(url, data=data)

        else:
            raise ValueError('Invalid HTTP method: "%s"' % method)

        if response.status_code == 401:
            raise IncorrectAPICredentials('Invalid TagCube API credentials')

        try:
            json_data = response.json()
        except ValueError:
            msg = 'TagCube REST API did not return JSON, if this issue'\
                  ' persists please contact support@tagcube.io'
            raise TagCubeAPIException(msg)

        pretty_json = json.dumps(json_data, indent=4)
        msg = 'Received %s HTTP response from the wire:\n%s'
        api_logger.debug(msg % (response.status_code, pretty_json))

        # Error handling
        self.handle_api_errors(response.status_code, json_data)

        return response.status_code, json_data

    def build_full_url(self, last_part):
        return '%s%s%s' % (self.root_url, self.API_VERSION, last_part)

    def build_api_path(self, resource_name, last_part=''):
        return '/%s/%s/%s' % (self.API_VERSION, resource_name, last_part)
