from collections import OrderedDict
from html.parser import HTMLParser
from xml.etree.ElementTree import fromstring as xml_from_string


# noinspection PyAbstractClass
class LoginInfoParser(HTMLParser):

    def __init__(self):
        super(LoginInfoParser, self).__init__()
        self.form_opened = False
        self._login_info = OrderedDict({
            'Uid': '',
            'Password': '',
        })

    @property
    def login_info(self):
        return self._login_info.copy()

    def handle_starttag(self, tag, attributes):
        if tag == 'form':
            # attribute_dict = {key: value for key, value in attributes}
            attribute_dict = dict(attributes)
            if 'id' in attribute_dict and attribute_dict['id'] == 'frmLogin':
                self.form_opened = True
                return

        if tag == 'input' and self.form_opened:
            # attribute_dict = {key: value for key, value in attributes}
            attribute_dict = dict(attributes)
            if 'type' in attribute_dict and attribute_dict['type'] == 'hidden':
                name = attribute_dict.get('name')
                value = attribute_dict.get('value', '')
                self._login_info[name] = value

    def handle_endtag(self, tag):
        if tag == 'form' and self.form_opened:
            self.form_opened = False


class LoginErrorCheckParser(object):
    @staticmethod
    def has_error_div(content):
        pattern = '<div id="PnlPwErrLogin">'
        return content.find(pattern) != -1


class OnAirAccessCheckParser(object):
    @staticmethod
    def is_granted(content):
        pattern = '<div class="player-body" id="media-player">'
        return content.find(pattern) != -1


class OnAirStreamingUrlParser(object):
    @staticmethod
    def parse(content):
        print(content)
        print()
        root = xml_from_string(content)
        rtmp_server = root[0].text.strip()
        media_url = root[2].text.strip()
        return rtmp_server + media_url


def extract_login_info(content):
    parser = LoginInfoParser()
    parser.feed(content)
    return parser.login_info


def check_login_error(content):
    return LoginErrorCheckParser.has_error_div(content)


def check_on_air_page(content):
    return OnAirAccessCheckParser.is_granted(content)


def extract_streaming_url(content):
    return OnAirStreamingUrlParser.parse(content)
