from datetime import datetime, timedelta

from unittest import TestCase
from unittest.mock import patch

from recorder import MPlayer
from recorder.urls import MbcRadioUrl
from recorder.utils import DirectoryCleaner

from operator import itemgetter
from os import listdir, stat
from os.path import abspath, isfile

from re import compile as re_compile


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


class TestDirectoryCleaner(TestCase):

    day_in_sec = 3600 * 24
    now = datetime.utcnow().timestamp()

    def setUp(self):
        self.dc = DirectoryCleaner()

        self.patch = patch('recorder.utils.DirectoryCleaner._grab_files')
        self.mock = self.patch.start()
        self.mock.return_value = [
            ('/home/tester/foo.txt', self.now - (self.day_in_sec * 8)),
            ('/home/tester/bar.txt', self.now - (self.day_in_sec * 55)),
            ('/home/tester/foobar.m4a', self.now - (self.day_in_sec * 60)),
            ('/home/tester/foo_bar_baz.m4a', self.now - (self.day_in_sec * 34)),
            ('/home/tester/IMG_2039.jpg', self.now - (self.day_in_sec * 20)),
            ('/home/tester/IMG_5040.png', self.now - (self.day_in_sec * 2)),
        ]

    def tearDown(self):
        self.patch.stop()

    def test_dir(self):
        """
        test with current directory
        """
        self.patch.stop()
        filtered = self.dc.dir('.').files()
        self.patch.start()

        # NOTE: default order_by: mtime, order: desc
        true_ans = [(abspath(x), stat(x).st_mtime) for x in filter(lambda x: isfile(x), listdir('.'))]
        true_ans.sort(key=itemgetter(1), reverse=True)

        self.assertListEqual(filtered, true_ans)

    def test_datetime_after(self):
        """
        after() method test.
        filter files newer than 30 days
        """
        filtered = self.dc.after({'days': 30}).files()
        ts = self.now - self.day_in_sec * 30
        for item in filtered:
            self.assertTrue(item[1] > ts)

    def test_datetime_before(self):
        """
        before method test.
        filter files older then a week
        """
        filtered = self.dc.before(timedelta(weeks=1)).files()
        ts = self.now - self.day_in_sec * 7
        for item in filtered:
            self.assertTrue(item[1] < ts)

    def test_limit(self):
        """
        limit files
        """
        num_limit = 3
        filtered = self.dc.limit(num_limit).files()
        self.assertEqual(len(filtered), num_limit)

    def test_reserve(self):
        """
        reserve files
        """
        num_reserve = 3
        all_items = self.dc.all().files()
        filtered = self.dc.reserve(num_reserve).files()
        self.assertEqual(len(filtered), len(all_items) - num_reserve)

    def test_all(self):
        """
        all() method test
        """
        # NOTE: default order_by: mtime, order: desc
        all_items = self.dc._grab_files('.', False)
        all_items.sort(key=itemgetter(1), reverse=True)

        filtered = self.dc.limit(1).reserve(3).all().files()
        self.assertEqual(filtered, all_items)

    def test_pattern(self):
        pattern = r'IMG_\d{4}\.(jpg|png)'
        r = re_compile(pattern)
        filtered = self.dc.pattern(pattern).files()
        for item in filtered:
            self.assertTrue(r.search(item[0]) is not None)

    def test_ext(self):
        """
        ext() method test
        """
        ext = '.m4a'
        filtered = self.dc.ext(ext).files()
        for item in filtered:
            self.assertTrue(item[0].endswith(ext))
