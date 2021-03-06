
class LoginFailedException(Exception):
    def __init__(self, msg):
        self.msg = msg


class InvalidPageNameException(Exception):
    pass


class AccessFailedException(Exception):
    pass


class AlreadyRecording(Exception):
    pass


class InvalidChannelException(Exception):
    pass
