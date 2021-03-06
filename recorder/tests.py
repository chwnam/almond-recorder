from argparse import Namespace

from datetime import (
    datetime,
    timedelta,
)

from http.client import HTTPMessage

from operator import itemgetter

from os import (
    getcwd,
    listdir,
    stat,
    unlink,
)

from os.path import (
    abspath,
    dirname,
    exists,
    isfile,
    join,
)

from random import randint
from re import compile as re_compile
from shutil import copy as shutil_copy

from time import (
    sleep,
    time,
)

from unittest import TestCase

from unittest.mock import (
    MagicMock,
    patch,
)

from urllib.parse import (
    urlparse,
    parse_qsl
)

from . import (
    backends,
    connectors,
    metadata,
    playlist,
    urls,
    utils,
)

import mbc_playlist


class TestBackends(TestCase):

    project_path = ''
    resource_path = ''

    def setUp(self):
        from os.path import dirname, join

        self.project_path = dirname(dirname(__file__))
        self.resource_path = join(self.project_path, 'recorder', 'resources', 'sample.mp3')

    def test_mplayer(self):
        """
        Mplayer backend test
        """
        m = backends.MPlayer()
        # NOTE: do not call stop(), use terminate()
        return_val = m.record(self.resource_path, 'a.m4a').wait(3).stop()

        self.assertEqual(return_val, 0)
        self.assertTrue(exists('a.m4a'))
        unlink('a.m4a')

    def test_ffprobe(self):
        """
        FFProbe backend test
        """
        p = backends.FFProbe()
        probed = p.probe(self.resource_path)

        self.assertEqual(probed.metadata.album, 'Farther Than All The Stars')
        self.assertEqual(probed.streams[0].codec_name, 'mp3')

    def test_ffmpeg(self):
        """
        FFMpeg backend test
        """
        title = 'Title changed by test'
        output = 'test_output.mp3'

        data = metadata.FFMpegMetadata()
        data.title = title

        f = backends.FFMpeg()
        return_value = f.insert_metadata(self.resource_path, data, output)
        self.assertEqual(return_value, 0)

        # check if the title is changed correctly
        p = backends.FFProbe()
        probed = p.probe(output)
        self.assertEqual(probed.metadata.title, title)
        unlink(output)


class TestDirectoryCleaner(TestCase):
    """
    DirectoryCleaner class test
    NOTE:
        - default order:    'desc'
        - default order_by: 'mtime'
        - files() returns:  [(name, mtime), ...]
    """
    day_in_sec = 3600 * 24
    now = datetime.utcnow().timestamp()

    def setUp(self):
        self.dc = utils.DirectoryCleaner()

        # Mocking _grab_files() method
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
        dir() method test
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
        after() method test
        filter files newer than 30 days
        """
        filtered = self.dc.after({'days': 30}).files()
        ts = self.now - self.day_in_sec * 30
        for item in filtered:
            self.assertTrue(item[1] > ts)

    def test_datetime_before(self):
        """
        before() method test
        filter files older then a week
        """
        filtered = self.dc.before(timedelta(weeks=1)).files()
        ts = self.now - self.day_in_sec * 7
        for item in filtered:
            self.assertTrue(item[1] < ts)

    def test_limit(self):
        """
        limit() method test
        """
        num_limit = 3
        filtered = self.dc.limit(num_limit).files()
        self.assertEqual(len(filtered), num_limit)

    def test_reserve(self):
        """
        reserve() method test
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
        """
        pattern() method test
        """
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


class TestConnectorMixin(TestCase):
    def test_create_get_url(self):
        """
        Test ConnectorMixin.create_get_url() method
        """
        params = {
            'var1': 'my_var',
            'var2': 'your_var',
        }

        # Test 1: encode params
        out = connectors.ConnectorMixin.create_get_url('http://www.example.com', params=params)
        query = dict(parse_qsl(urlparse(out).query))
        self.assertDictEqual(params, query)

        # Test 2: some of parameters are in the param argument, and the others are already encoded in the url string
        p = params.copy()
        del (p['var1'])
        out = connectors.ConnectorMixin.create_get_url('http://www.example.com?var1=my_var', params=p)
        query = dict(parse_qsl(urlparse(out).query))
        self.assertDictEqual(params, query)

    def test_detect_charset(self):
        """
        Test ConnectorMixin.detect_charset() method
        """

        # Test 1
        # Encoding data is in the response header, get_content_charset() returns an encoding.
        headers = HTTPMessage()
        headers.get_content_charset = MagicMock(return_value='euc-kr')
        charset = connectors.ConnectorMixin.detect_charset(headers, b'')
        self.assertEqual('euc-kr', charset)

        # Test 2
        # Sometimes response does not have 'Content-Type' header.
        # Find meta tag in the content: <meta charset="...">
        headers.get_content_charset = MagicMock(return_value='')
        content = b'<html><head><meta charset="utf-16"></head></html>'
        charset = connectors.ConnectorMixin.detect_charset(headers, content)
        self.assertEqual('utf-16', charset)

        # Test 3
        # <meta http-equiv ... > style tag
        headers.get_content_charset = MagicMock(return_value='')
        content = b"""
          <html>
          <head>
            <meta http-equiv="Content-Type" content="text/html; charset=test-encoding">
          </head>
          </html>
        """
        charset = connectors.ConnectorMixin.detect_charset(headers, content)
        self.assertEqual('test-encoding', charset)

        # Test 4
        # Test if fallback encoding is correctly returned
        headers.get_content_charset = MagicMock(return_value='')
        content = b"""<html><head></head></html>"""
        charset = connectors.ConnectorMixin.detect_charset(headers, content, 'fallback-encoding')
        self.assertEqual('fallback-encoding', charset)


class TestRequestsConnector(TestCase):

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


class TestUrls(TestCase):

    def setUp(self):
        self.test_mbc_available = utils.check_connection(
            urlparse(urls.MbcRadioUrl.url_base).netloc
        )

    def test_mbc_fm4u(self):

        if self.test_mbc_available:

            mbc = urls.MbcRadioUrl()

            url = mbc.mfm()
            self.assertTrue(url.startswith('rtmp://'))
            sleep(3)

            url = mbc.sfm()
            self.assertTrue(url.startswith('rtmp://'))
            sleep(3)

            url = mbc.chm()
            self.assertTrue(url.startswith('rtmp://'))
            sleep(3)


def get_yesterday():
    return (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')


def mbc_choose_any_program(table_path):
    """
    randomly select one item of MBCRadioProgramTable
    :param table_path:
    :return:
    """
    table = playlist.MBCRadioProgramTable(table_path=table_path)
    programs = list(filter(lambda x: x.playlist_slug, table.programs))
    random_id = randint(0, len(programs) - 1)

    if programs:
        return programs[random_id]


class TestPlaylist(TestCase):

    def setUp(self):
        self.table_path = join(abspath(getcwd()), 'test_table.csv')

    def tearDown(self):
        if exists(self.table_path):
            unlink(self.table_path)

    def test_mbc_radio_program_table(self):

        if exists(self.table_path):
            unlink(self.table_path)

        table = playlist.MBCRadioProgramTable(table_path=self.table_path)

        self.assertEqual(self.table_path, table.table_path)
        self.assertTrue(exists(table.table_path))
        self.assertTrue(table.version > 0)
        self.assertTrue(len(table.programs) > 0)

    def test_mbc_radio_playlist_crawler(self):

        program = mbc_choose_any_program(self.table_path)
        if program:
            # check view url validity
            crawler = playlist.MBCRadioPlaylistCrawler()
            yesterday = get_yesterday()
            view_url = crawler.get_view_url(program, yesterday)
            self.assertTrue(view_url.startswith('http') and len(view_url) > 0)

            # check playlist item validity
            program_playlist = crawler.extract_playlist(view_url)
            if len(program_playlist) > 0:
                first_item = program_playlist[0]
                self.assertTrue('seq' in first_item)
                self.assertTrue('title' in first_item)
                self.assertTrue('artist' in first_item)


class TestMBCPlaylistScript(TestCase):

    def setUp(self):
        self.table_path = join(abspath(getcwd()), 'test_table.csv')

    def tearDown(self):
        if exists(self.table_path):
            unlink(self.table_path)

    @patch('mbc_playlist.ArgumentParser.parse_args')
    def test_run(self, mocked_parse_args):
        """
        MBCPlaylistScript.run() test
        """

        # preparing mocked argument parsing
        current_dir = dirname(__file__)
        random_program = mbc_choose_any_program(self.table_path)
        yesterday = get_yesterday()
        sample_file = join(current_dir, 'resources', 'sample.mp3')
        output_file = join(current_dir, 'resources', 'sample_tested.mp3')

        expected_args = Namespace(
            input=sample_file,
            output=output_file,
            playlist_date=yesterday,
            program_id=random_program.id,
            table_path=self.table_path,
            ffmpeg_path=None,
            list_programs=False,
            update_table=False,
            version=False,
            print_only=False,
            replace=False
        )

        # mocking done
        mocked_parse_args.return_value = expected_args

        mbc_playlist.MBCPlaylistScript().run()

        # output should exist
        self.assertTrue(exists(output_file))

        # if ffprobe is available, also test this.
        # metadata's description should equal to crawled text
        if exists(backends.FFPROBE_PATH):
            crawler = playlist.MBCRadioPlaylistCrawler()
            pl = crawler.get_playlist(random_program.id, yesterday)
            pl_text = mbc_playlist.MBCPlaylist.format_text(pl)

            probe = backends.FFProbe()
            md = probe.probe(output_file)

            self.assertEqual(pl_text, md.metadata.description)

        unlink(output_file)

    @patch('mbc_playlist.ArgumentParser.parse_args')
    def test_run_replace(self, mocked_parse_args):
        """
        MBCPlaylistScript.run() test. --replace is used.
        """

        # preparing mocked argument parsing
        current_dir = dirname(__file__)
        random_program = mbc_choose_any_program(self.table_path)
        yesterday = get_yesterday()
        sample_file = join(current_dir, 'resources', 'sample.mp3')
        input_file = join(current_dir, 'resources', 'sample_for_replace_test.mp3')

        # copy file
        shutil_copy(sample_file, input_file)
        self.assertTrue(exists(input_file))
        del sample_file

        expected_args = Namespace(
            input=input_file,
            output=None,
            playlist_date=yesterday,
            program_id=random_program.id,
            table_path=self.table_path,
            ffmpeg_path=None,
            list_programs=False,
            update_table=False,
            version=False,
            print_only=False,
            replace=True  # replace
        )

        # mocking done
        mocked_parse_args.return_value = expected_args

        mbc_playlist.MBCPlaylistScript().run()

        # if ffprobe is available, also test this.
        # metadata's description should equal to crawled text
        if exists(backends.FFPROBE_PATH):
            crawler = playlist.MBCRadioPlaylistCrawler()
            pl = crawler.get_playlist(random_program.id, yesterday)
            pl_text = mbc_playlist.MBCPlaylist.format_text(pl)

            probe = backends.FFProbe()
            md = probe.probe(input_file)

            self.assertEqual(pl_text, md.metadata.description)

        unlink(input_file)
