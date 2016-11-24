import unittest
from http.client import HTTPMessage
from os import unlink
from os.path import exists
from time import time
from unittest.mock import MagicMock
from urllib.parse import urlparse, parse_qsl

from recorder import connectors, urls
from ..bots import urls


class TestConnectorMixin(unittest.TestCase):
    def test_create_get_url(self):
        params = {
            'var1': 'my_var',
            'var2': 'your_var',
        }
        out = connectors.ConnectorMixin.create_get_url('http://www.example.com', params=params)
        query = dict(parse_qsl(urlparse(out).query))
        self.assertDictEqual(params, query)

        p = params.copy()
        del (p['var1'])
        out = connectors.ConnectorMixin.create_get_url('http://www.example.com?var1=my_var', params=p)
        query = dict(parse_qsl(urlparse(out).query))
        self.assertDictEqual(params, query)

    def test_detect_charset(self):
        headers = HTTPMessage()
        headers.get_content_charset = MagicMock(return_value='euc-kr')
        charset = connectors.ConnectorMixin.detect_charset(headers, b'')
        self.assertEqual('euc-kr', charset)

        headers.get_content_charset = MagicMock(return_value='')
        content = b'<html><head><meta charset="utf-16"></head></html>'
        charset = connectors.ConnectorMixin.detect_charset(headers, content)
        self.assertEqual('utf-16', charset)

        headers.get_content_charset = MagicMock(return_value='')
        content = b"""
          <html>
          <head>
            <meta http-equiv="Content-Type" content="text/html; charset=test-encoding">
          </head>
          </html>
        """
        charset = web.ConnectorMixin.detect_charset(headers, content)
        self.assertEqual('test-encoding', charset)

        headers.get_content_charset = MagicMock(return_value='')
        content = b"""<html><head></head></html>"""
        charset = connectors.ConnectorMixin.detect_charset(headers, content, 'fallback-encoding')
        self.assertEqual('fallback-encoding', charset)


class TestRequestsConnector(unittest.TestCase):

    cookie_file = 'test.cookie'

    def setUp(self):
        self.create_test_cookie_file()

    def tearDown(self):
        self.delete_cookie_file()

    def test_connector(self):
        connector = connectors.RequestsConnector(self.cookie_file, )

        # cookie save test
        connector.set_cookie('test', 'val', domain='test.com', path='/', expires=time() + 3600, discard=False)
        connector.save_cookie('temp-file.cookie')
        with open('temp-file.cookie', 'r') as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[1].strip().startswith('Set-Cookie3:'))
        self.delete_cookie_file('temp-file.cookie')

        # connection test
        response = connector.get('http://www.google.com')
        self.assertIsInstance(response, str)
        self.assertTrue(len(response) > 0)

    @classmethod
    def create_test_cookie_file(cls):
        cls.delete_cookie_file()
        with open(cls.cookie_file, 'w') as f:
            f.write('#LWP-Cookies-2.0\n')

    @classmethod
    def delete_cookie_file(cls, file_name=None):
        if not file_name:
            file_name = cls.cookie_file
        if exists(file_name):
            unlink(file_name)


class TestUrls(unittest.TestCase):
    def test_mbc_fm4u(self):
        mbc = urls.MbcRadioUrl()
        url = mbc.fm4u()
        self.assertTrue(url.startswith('rtmp://'))
