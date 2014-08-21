import unittest
import httpretty
import json

from tagcube.client.api import TagCubeClient


class TestTagCubeClient(unittest.TestCase):

    ROOT_URL = TagCubeClient.DEFAULT_ROOT_URL
    API_VERSION = TagCubeClient.API_VERSION
    EMAIL = 'foo@bar.com'
    API_KEY = 'f364b098-0fb3-4178-a45b-883f389ad294'
    TARGET_DOMAIN = 'target.com'

    def setUp(self):
        super(TestTagCubeClient, self).setUp()

        self.client = TagCubeClient(self.EMAIL, self.API_KEY)
        #self.client.set_verbose(True)

    @httpretty.activate
    def test_credentials_content_type_basic_request(self):
        url = "%s%s/profiles/" % (self.ROOT_URL, self.API_VERSION)
        httpretty.register_uri(httpretty.GET, url, body='[]',
                               content_type="application/json")

        scan_profile_resource = self.client.get_scan_profile('fast_scan')

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

        scan_profile_resource = self.client.get_scan_profile('fast_scan')

        self.assertEqual(scan_profile_resource, json.loads(expected_json))

    @httpretty.activate
    def test_get_scan_profile_not_exists(self):
        url = "%s%s/profiles/" % (self.ROOT_URL, self.API_VERSION)

        httpretty.register_uri(httpretty.GET, url, body='[]',
                               content_type="application/json")

        scan_profile_resource = self.client.get_scan_profile('fast_scan')

        self.assertEqual(scan_profile_resource, None)

    @httpretty.activate
    def test_quick_scan_invalid_profile(self):
        url = "%s%s/profiles/" % (self.ROOT_URL, self.API_VERSION)

        httpretty.register_uri(httpretty.GET, url, body='[]',
                               content_type="application/json")

        self.assertRaises(ValueError, self.client.quick_scan, self.ROOT_URL,
                          scan_profile='not_exists')

    @httpretty.activate
    def test_domain_add(self):
        url = "%s%s/domains/" % (self.ROOT_URL, self.API_VERSION)

        _json = {"id": 2,
                 "description": "A description",
                 "domain": "target.com",
                 "href": "/1.0/domains/2",
                 "state": "pending-verification",
                 "verification_code": "46e06dde-43c6-4b31-88bd-6a0ffea42261"}

        httpretty.register_uri(httpretty.POST, url, body=json.dumps(_json),
                               content_type="application/json", status=201)

        domain_resource = self.client.domain_add(self.TARGET_DOMAIN,
                                                 'A description')

        # pylint: disable=E1101
        self.assertEqual(domain_resource.id, 2)
        self.assertEqual(domain_resource.href, '/1.0/domains/2')
        # pylint: enable=E1101

        request = httpretty.last_request()

        self.assertEqual(request.method, 'POST')
        self.assertEqual(request.body, '{"domain": "target.com", '
                                       '"description": "A description"}')
        self.assertEqual(request.path, '/1.0/domains/')

    @httpretty.activate
    def test_get_email_notification_exists(self):
        url = "%s%s/notifications/email/" % (self.ROOT_URL, self.API_VERSION)
        expected_json = '''\
        {
            "description": "Notification email",
            "email": "abc@def.com",
            "first_name": "Andres",
            "href": "/1.0/notifications/email/1",
            "id": 1,
            "last_name": "Riancho"
        }
        '''
        body = '[%s]' % expected_json
        httpretty.register_uri(httpretty.GET, url, body=body,
                               content_type="application/json")

        email_resource = self.client.get_email_notification('abc@def.com')

        self.assertEqual(email_resource, json.loads(expected_json))

    @httpretty.activate
    def test_get_email_notification_not_exists(self):
        url = "%s%s/notifications/email/" % (self.ROOT_URL, self.API_VERSION)

        httpretty.register_uri(httpretty.GET, url, body='[]',
                               content_type="application/json")

        email_resource = self.client.get_email_notification('abc@def.com')

        self.assertEqual(email_resource, None)

    @httpretty.activate
    def test_email_notification_add(self):
        url = "%s%s/notifications/email/" % (self.ROOT_URL, self.API_VERSION)
        post_answer = '''
        {
            "description": "Notification email",
            "email": "abc@def.com",
            "first_name": "Andres",
            "href": "/1.0/notifications/email/1",
            "id": 1,
            "last_name": "Riancho"
        }'''

        httpretty.register_uri(httpretty.POST, url, body=post_answer,
                               content_type="application/json", status=201)

        email_resource = self.client.email_notification_add('abc@def.com',
                                                            'Andres', 'Riancho',
                                                            'Notification email')

        # pylint: disable=E1101
        self.assertEqual(email_resource.id, 1)
        self.assertEqual(email_resource.href,
                         '/%s/notifications/email/1' % self.API_VERSION)
        # pylint: enable=E1101

        expected_sent_json = '''\
        {
            "description": "Notification email",
            "email": "abc@def.com",
            "first_name": "Andres",
            "last_name": "Riancho"
        }
        '''

        request = httpretty.last_request()

        self.assertEqual(request.method, 'POST')
        self.assertEqual(json.loads(request.body), json.loads(expected_sent_json))
        self.assertEqual(request.path, '/1.0/notifications/email/')

    @httpretty.activate
    def test_get_domain_exists(self):
        url = "%s%s/domains/" % (self.ROOT_URL, self.API_VERSION)
        expected_json = '''\
        {
            "domain": "www.fogfu.com",
            "href": "/1.0/domains/2",
            "id": 2,
            "state": "pending-verification",
            "verification_code": "46e06dde-43c6-4b31-88bd-6a0ffea42261"
        }
        '''
        body = '[%s]' % expected_json
        httpretty.register_uri(httpretty.GET, url, body=body,
                               content_type="application/json")

        domain_resource = self.client.get_domain('www.fogfu.com')

        self.assertEqual(domain_resource, json.loads(expected_json))

    @httpretty.activate
    def test_get_domain_not_exists(self):
        url = "%s%s/domains/" % (self.ROOT_URL, self.API_VERSION)

        httpretty.register_uri(httpretty.GET, url, body='[]',
                               content_type="application/json")

        domain_resource = self.client.get_domain('www.fogfu.com')

        self.assertEqual(domain_resource, None)
