from recorder.connectors import RequestsConnector, UserAgents
from .pages import LoginPage


class MbcOnAirTv(object):

    def __init__(self):
        extra_headers = {
            'User-Agents': UserAgents.firefox(),
        }

        self.connector = RequestsConnector(
            cookie_file='changwoo.cookie',
            extra_headers=extra_headers
        )

    def streaming_url(self, user_id, user_password):

        return LoginPage(self.connector)\
            .login(user_id, user_password)\
            .to_tv_on_air_page()\
            .get_streaming_url()
