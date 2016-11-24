from unittest import TestCase

from recorder import MPlayer
from recorder.urls import MbcRadioUrl


class TestMplayerBackend(TestCase):
    def test_mplayer_backend(self):

        from time import sleep
        from os.path import exists
        from os import unlink

        url = MbcRadioUrl()
        fm4u = url.fm4u()

        m = MPlayer()
        m.record(fm4u, 'a.m4a')
        sleep(5)
        m.stop()

        self.assertTrue(exists('a.m4a'))
        unlink('a.m4a')
