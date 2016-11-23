from .connectors import BasicConnector


class MbcRadioUrls(object):

    def __init__(self):
        self.connector = BasicConnector()

    def standard_fm(self):
        pass

    def fm4u(self):
        pass

    def channel_m(self):
        pass

    def __request(self, channel):
        pass


class KbsRadioUrls(object):
    pass


class SbsRadioUrls(object):
    pass


class EbsRadioUrls(object):
    pass
