from recorder.bots import (
    AccessFailedException,
    InvalidPageNameException,
    LoginFailedException,
)
from recorder.bots import RequestsConnector
from .parsers import (
    extract_login_info,
    extract_streaming_url,
    check_login_error,
    check_on_air_page
)


class BasePage(object):
    pages = {
        'tv-on-air': 'TvOnAirPage',
        'login': 'LoginPage',
        'logout': 'LogoutPage',
    }

    url = ''

    def __init__(self, connector: RequestsConnector):
        self.connector = connector

    def visit(self):
        return self.connector.get(self.url)

    def go_to(self, page: str):
        if page not in self.pages:
            raise InvalidPageNameException()
        return globals()[self.pages[page]](self.connector)

    def to_login_page(self):
        return self.go_to('login')

    def to_logout_page(self):
        return self.go_to('logout')

    def to_tv_on_air_page(self):
        return self.go_to('tv-on-air')

    @property
    def is_logged_in(self):
        cookie = self.connector.get_cookie('IMBCSession')
        return cookie is not None


class LoginPage(BasePage):
    url = 'http://member.imbc.com/Login/Login.aspx'
    action = 'https://member.imbc.com/Login/LoginProcess.aspx'

    def login(self, user_id, user_password):
        login_data = self._get_login_parameters()
        login_data['Uid'] = user_id
        login_data['Password'] = user_password

        content = self.connector.post(self.action, data=login_data)

        if not self._check_login(content):
            raise LoginFailedException('Login has failed!')

        return self

    def _get_login_parameters(self):
        content = self.connector.get(self.url)

        return extract_login_info(content)

    def _check_login(self, content):
        login_failed = check_login_error(content)

        return self.is_logged_in and not login_failed


class TvOnAirPage(BasePage):
    url = 'http://vodmall.imbc.com/player/onair.aspx'
    stream_info_url = 'http://vodmall.imbc.com/util/player/onairurlutil_secure.ashx'

    def _check_access(self):
        content = self.visit()
        access_granted = check_on_air_page(content)

        return self.is_logged_in and access_granted

    def get_streaming_url(self):
        if not self._check_access():
            raise AccessFailedException()

        content = self.connector.post(self.stream_info_url)

        return extract_streaming_url(content)


class LogoutPage(BasePage):
    url = 'http://member.imbc.com/Login/Logout.aspx'
