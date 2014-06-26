import requests
import logging
import json


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