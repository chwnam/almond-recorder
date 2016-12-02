from http.cookiejar import LWPCookieJar, LoadError
from http.client import HTTPMessage
from re import (
    compile as re_compile,
    IGNORECASE
)
from os.path import exists as path_exists
from time import sleep
from urllib.parse import urlencode, parse_qsl
from urllib.request import (
    build_opener,
    HTTPCookieProcessor,
    Request,
    urlopen
)
from http.cookiejar import Cookie
import requests

meta_equiv_expr = re_compile(b'<meta.*?http-equiv="content-type".*?content="(.+);\s*charset=(.+)".*>', IGNORECASE)
meta_expr = re_compile(b'<meta\s+.*?(charset="(.+?)").*?>')
charset_expr = re_compile(r'(.+)\s*;\s+charset=([^\s]+)')


class ConnectorMixin(object):
    """
    Connector mixin
    """

    @staticmethod
    def create_get_url(url: str, params: dict = None):
        """
        Creates a url for a GET request.
        params argument is encoded and appended to url.
        Query strings already existing in the url are also preserved.
        """
        if not url:
            return ''
        if not params:
            params = {}

        query_index = url.rfind('?')
        if query_index > -1:
            params.update(parse_qsl(url[query_index + 1:]))
            url = url[:query_index]

        return url + ('' if not params else '?' + urlencode(params))

    @staticmethod
    def detect_charset(headers, content, fallback_charset='utf-8'):
        """
        Detect charset using headers or content text, returns fallback charset if none is found.
         fallback_charset can be a string or a list.
        """
        if isinstance(headers, HTTPMessage):
            # response is made via urllib
            # charset is in the Content-Type header
            charset_in_header = headers.get_content_charset()
            if charset_in_header:
                return charset_in_header

        # damn! content-type header not found!
        # charset is in the content. Let's parse
        meta_found = meta_expr.search(content)
        if meta_found:
            # <meta charset="...."> found
            return meta_found.group(2).decode('ascii')

        meta_equiv_found = meta_equiv_expr.search(content)
        if meta_equiv_found:
            # <meta http-equiv="Content-Type" content="text/html; charset=...."> found
            return meta_equiv_found.group(2).decode('ascii')

        return fallback_charset


class BaseConnector(object):
    """
    Connector base class
    """

    def __init__(self, delay=3, extra_headers=None):
        """
        Keywords
        --------
        delay: mandatory halt after each response. May be zero.
        extra_headers: dict for additional request headers
        """
        self._delay = delay
        self._extra_headers = extra_headers or {}
        self._last_content = ''

    def request(self, url, method='GET', params=None, data=None, headers=None):
        raise NotImplemented()

    def get(self, url, params=None, headers=None):
        return self.request(url, method='GET', params=params, headers=headers)

    def post(self, url, data=None, headers=None):
        return self.request(url, method='POST', data=data, headers=headers)

    def save_last_content(self, file_name):
        with open(file_name, 'w') as f:
            f.write(self._last_content)


class BasicConnector(ConnectorMixin, BaseConnector):
    """
    BasicConnector is a naive connector implemented by using python urllib. Useful for simple GET/POST requests.
    As cookie is NOT supported, you may want to use SimpleCookieConnector, or RequestsConnector
    """

    def __init__(self, delay=0, extra_headers=None, fallback_charset='utf-8'):
        """
        Keywords
        --------
         - fallback_charset: a string or a list. Used when no charset hint is found.
        """
        super(BasicConnector, self).__init__(delay, extra_headers)
        self.fallback_charset = fallback_charset

    def request(self, url, method='GET', params=None, data=None, headers=None):

        headers = (headers or {})
        headers.update(self._extra_headers)

        if method.upper() == 'GET':
            request = Request(
                url=self.create_get_url(url, params),
                headers=headers
            )
        elif method.upper() == 'POST':
            request = Request(
                url=url,
                data=bytes(urlencode(data), 'utf-8'),
                headers=headers)
        else:
            raise AttributeError('GET or POST is allowed.')

        response = urlopen(request)
        raw_content = response.read()
        response.close()

        charset = self.detect_charset(
            headers=response.headers,
            content=raw_content,
            fallback_charset=self.fallback_charset
        )

        # decode response content by charset
        if isinstance(charset, str):
            return raw_content.decode(charset)
        elif isinstance(charset, list):
            for c in charset:
                try:
                    return raw_content.decode(c)
                except UnicodeDecodeError:
                    pass

        raise UnicodeDecodeError()


class SimpleCookieConnector(ConnectorMixin, BaseConnector):
    def __init__(self, cookie_file, delay=3, extra_headers=None):
        """
        Keywords
        --------
         - cookie_file
        """
        super(SimpleCookieConnector, self).__init__(delay, extra_headers)

        self._cookie_file = cookie_file
        self._cookie_jar = LWPCookieJar(filename=self._cookie_file)
        self._cookie_processor = HTTPCookieProcessor(self._cookie_jar)

        self._opener = build_opener(self._cookie_processor)

        self._last_request = None
        self._last_response = None
        self._last_content = ''

    def request(self, url, method='GET', params=None, data=None, headers=None):

        if not url:
            return ''

        params = params or {}
        data = data or {}
        headers = (headers or {}).update(self._extra_headers)

        if method.upper() == 'GET':
            _url = self.create_get_url(url, params)
            return self.resolve(Request(_url, data=None, headers=headers))

        elif method.upper() == 'POST':
            return self.resolve(Request(url, data=bytes(urlencode(data), 'utf-8'), headers=headers))

    def resolve(self, request):
        self._last_request = request
        self._last_response = self._opener.open(self._last_request)
        content = self._last_response.read()
        self._last_response.close()
        sleep(self._delay)

        charset = self.detect_charset(headers=self._last_response.headers, content=content)
        self._last_content = content.decode(charset)

        return self._last_content

    def save_cookie(self):
        self._cookie_jar.save(self._cookie_file)

    def get_cookie(self, name):
        for cookie in self._cookie_jar:
            if cookie.name == name:
                return cookie
        return None


class RequestsConnector(BaseConnector):
    """
    Connector implemented with requests library, more robust and advanced.
    """

    def __init__(self, cookie_file, delay=3, extra_headers=None):
        """
        Keywords
        --------
         - cookie_file
        """
        super(RequestsConnector, self).__init__(delay, extra_headers)

        self._cookie_file = cookie_file
        self._cookie_jar = requests.cookies.RequestsCookieJar()
        self._last_response = None

        self.load_cookie()

    def request(self, url, method='GET', params=None, data=None, headers=None):
        headers = headers or {}
        headers.update(self._extra_headers)
        self._last_response = requests.request(
            url=url,
            method=method,
            params=params,
            data=data,
            headers=headers,
            cookies=self._cookie_jar
        )
        self._last_content = self._last_response.text
        self._cookie_jar.update(self._last_response.cookies)
        sleep(self._delay)

        return self._last_content

    def save_cookie(self, file_name=None, **kwargs):
        file_name = file_name or self._cookie_file
        lwp_jar = LWPCookieJar()
        for item in self._cookie_jar:
            args = dict(vars(item).items())
            args['rest'] = args['_rest']
            del (args['_rest'])
            cookie = Cookie(**args)
            lwp_jar.set_cookie(cookie)
        lwp_jar.save(file_name, **kwargs)

    def load_cookie(self, file_name=None, **kwargs):
        file_name = file_name or self._cookie_file
        if path_exists(file_name):
            try:
                lwp_jar = LWPCookieJar()
                lwp_jar.load(file_name, **kwargs)
                self._cookie_jar.update(lwp_jar)
            except LoadError:
                raise Exception('oops!')
                pass

    def get_cookie(self, name, default=None):
        return self._cookie_jar.get(name, default)

    def set_cookie(self, name, value, **kwargs):
        self._cookie_jar.set(name, value, **kwargs)


class UserAgents:
    """
    Sample user agent strings.
    """

    @staticmethod
    def firefox():
        return 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:50.0) Gecko/20100101 Firefox/50.0'

    @staticmethod
    def chrome():
        return 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) ' + \
               'Ubuntu Chromium/53.0.2785.143 Chrome/53.0.2785.143 Safari/537.36'
