import requests
import logging
import json

# These two lines enable debugging at httplib level
# (requests->urllib3->http.client) You will see the REQUEST, including HEADERS
# and DATA, and RESPONSE with HEADERS but without DATA.
# The only thing missing will be the response.body which is not logged.
try:
    import http.client as http_client
except ImportError:
    # Python 2
    import httplib as http_client


from tagcube.utils.urlparsing import get_domain_from_url, get_port_from_url

CAN_NOT_SCAN_DOMAIN_ERROR = '''\
You can't scan the specified domain. This happens in the following cases:

 * The current plan only allows scans to verified domains => Verify your domain
 ownership using TagCube's web UI or the REST API.

 * The domain quota for your plan has been exceeded => Upgrade your plan to be
 able to scan more domains.

'''


class TagCubeClient(object):

    ROOT_URL = 'https://api.tagcube.io/'
    API_VERSION = '1.0'
    SELF_URL = '/users/~'
    DOMAINS = '/domains/'
    SCAN_PROFILES = '/profiles/'
    DESCRIPTION = 'Created by TagCube REST API client'

    def __init__(self, email, api_key, verbose=False):
        self.email = email
        self.api_key = api_key
        self.session = None

        self.set_verbose(verbose)
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
            _, domain_resource = self.domain_add(domain)

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

        This method's last step is to send a POST request to /1.0/scans/ using
        a post-data similar to:

            {"verifications_href": "/1.0/verifications/6",
             "profiles_href": "/1.0/profiles/2",
             "start_time": "now",
             "email_notifications_href": [],
             "path_list": ["/"]}'

        :return: The newly generated scan id
        """
        raise NotImplementedError

    def get_scan_profile(self, scan_profile):
        """
        :return: The scan profile resource (as json), or None
        """
        return self.filter_resource('profiles', 'name', scan_profile)

    def filter_resource(self, resource_name, field_name, field_value):
        """
        :return: The resource (as json), or None
        """
        url = self.build_url('/%s/?%s=%s' % (resource_name, field_name,
                                             field_value))
        code, json = self.send_request(url)

        if len(json) == 1:
            return json[0]

        return None

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
        url = self.build_url('/notifications/email/')
        return self.create_resource(url, data)

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
        return self.filter_resource('domain', 'domain', domain)

    def domain_add(self, domain, description=DESCRIPTION):
        """
        Sends a POST to /1.0/domains/ using this post-data:

            {"domain": "www.fogfu.com",
             "description":"Added by tagcube-api"}

        :param domain: The domain name to add as a new resource
        :return: The newly created domain id
        """
        data = {"domain": domain,
                "description": description}
        url = self.build_url(self.DOMAINS)
        return self.create_resource(url, data)

    def create_resource(self, url, data):
        """
        Shortcut for creating a new resource
        :return: The newly created domain id
        """
        status_code, json_data = self.send_request(url, data, method='POST')
        try:
            return str(json_data['id']), json_data['href']
        except KeyError:
            # Parse the error and raise an exception, errors look like:
            # {u'error': [u'The domain foo.com already exists.']}
            error_string = u' '.join(json_data['error'])
            raise TagCubeAPIException(error_string)

    def set_verbose(self, verbose):
        level = logging.DEBUG if verbose else logging.CRITICAL
        http_client.HTTPConnection.debuglevel = 1 if verbose else 0

        logging.basicConfig()
        logging.getLogger().setLevel(level)

        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(level)
        requests_log.propagate = True

        requests_log = logging.getLogger("requests")
        requests_log.setLevel(level)

    def configure_requests(self):
        self.session = requests.Session()
        self.session.auth = (self.email, self.api_key)

        headers = {'Content-Type': 'application/json',
                   'User-Agent': 'TagCubeClient %s' % self.API_VERSION}
        self.session.headers.update(headers)

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

        return response.status_code, response.json()

    def build_url(self, last_part):
        return '%s%s%s' % (self.ROOT_URL, self.API_VERSION, last_part)


class TagCubeAPIException(Exception):
    pass


class IncorrectAPICredentials(Exception):
    pass