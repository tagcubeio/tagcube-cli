import requests
import logging
import json


class TagCubeClient(object):

    ROOT_URL = 'https://www.tagcube.io/'

    def __init__(self, email, api_key):
        self.email = email
        self.api_key = api_key
        self.session = None
        self.configure_requests()

    def test_auth_credentials(self):
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
