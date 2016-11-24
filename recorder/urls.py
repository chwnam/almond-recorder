from json import loads as json_loads
from re import compile as re_compile, MULTILINE, DOTALL

from recorder.connectors import BasicConnector


class MbcRadioUrl(object):

    expr = re_compile(r'\((.+)\);', MULTILINE | DOTALL)

    url_base = 'http://miniplay.imbc.com/WebLiveURL.ashx?channel={}&protocol=RTMP'

    def __init__(self):
        self.connector = BasicConnector()

    def standard_fm(self):
        return self._request('sfm')

    def fm4u(self):
        return self._request('mfm')

    def channel_m(self):
        return self._request('chm')

    def _request(self, channel):
        content = self.connector.get(url=self.url_base.format(channel))
        return self.trim_response(content)

    def trim_response(self, content):
        mat = self.expr.match(content)
        if mat:
            obj = json_loads(mat.group(1))
            return obj['AACLiveURL']

        raise KeyError('Invalid format response acquired.')


class KbsRadioUrls(object):
    pass


class SbsRadioUrls(object):
    pass


class EbsRadioUrls(object):
    pass
