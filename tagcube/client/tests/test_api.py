import unittest
import httpretty
import json

from tagcube.client.api import TagCubeClient


class TestTagCubeClient(unittest.TestCase):

    ROOT_URL = TagCubeClient.ROOT_URL
    API_VERSION = TagCubeClient.API_VERSION
    EMAIL = 'foo@bar.com'
    API_KEY = 'f364b098-0fb3-4178-a45b-883f389ad294'

    @httpretty.activate
    def test_credentials_content_type_basic_request(self):
        url = "%s%s/profiles/" % (self.ROOT_URL, self.API_VERSION)
        httpretty.register_uri(httpretty.GET, url, body='[]',
                               content_type="application/json")

        c = TagCubeClient(self.EMAIL, self.API_KEY)
        scan_profile_resource = c.get_scan_profile('fast_scan')

        self.assertEqual(scan_profile_resource, None)

        request = httpretty.last_request()
        self.assertEqual(request.method, 'GET')
        self.assertEqual(request.body, '')
        self.assertEqual(request.querystring, {u'name': [u'fast_scan']})
        self.assertEqual(request.path, '/1.0/profiles/?name=fast_scan')
        self.assertEqual(request.headers['content-type'], 'application/json')

        basic_auth = 'Basic Zm9vQGJhci5jb206ZjM2NGIwOTgtMGZiMy00MTc4LWE0NWItODgzZjM4OWFkMjk0'
        self.assertEqual(request.headers['authorization'], basic_auth)

    @httpretty.activate
    def test_get_scan_profile_exists(self):
        url = "%s%s/profiles/" % (self.ROOT_URL, self.API_VERSION)
        expected_json = '{"href": "/1.0/profiles/1","name": "full_audit"}'
        body = '[%s]' % expected_json
        httpretty.register_uri(httpretty.GET, url, body=body,
                               content_type="application/json")

        c = TagCubeClient(self.EMAIL, self.API_KEY)
        scan_profile_resource = c.get_scan_profile('fast_scan')

        self.assertEqual(scan_profile_resource, json.loads(expected_json))

    @httpretty.activate
    def test_get_scan_profile_not_exists(self):
        url = "%s%s/profiles/" % (self.ROOT_URL, self.API_VERSION)

        httpretty.register_uri(httpretty.GET, url, body='[]',
                               content_type="application/json")

        c = TagCubeClient(self.EMAIL, self.API_KEY)
        scan_profile_resource = c.get_scan_profile('fast_scan')

        self.assertEqual(scan_profile_resource, None)
