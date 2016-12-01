from bs4 import BeautifulSoup
from csv import reader as csv_reader
from datetime import datetime
from os import getcwd
from os.path import (
    abspath,
    exists as path_exists,
    join as path_join,
)
from re import compile as re_compile
from .connectors import BasicConnector


class RadioProgramItem(object):
    id = None
    start_time = ''
    show_title = ''


class MBCRadioProgramItem(RadioProgramItem):
    channel = ''
    homepage_slug = ''
    playlist_slug = ''

    url_prefix = 'http://mini.imbc.com/manager/'

    @property
    def homepage_url(self):
        if self.homepage_slug:
            url_base = 'http://www.imbc.com/broad/radio/%s'
            return url_base % self.homepage_slug

    @property
    def playlist_list_url(self):
        if self.playlist_slug:
            url_base = self.url_prefix + 'SelectList.asp?PROG_CD=%s'
            return url_base % self.playlist_slug

    @property
    def playlist_view_url(self):
        if self.playlist_slug:
            url_base = self.url_prefix + 'SelectView.asp?PROG_CD=%s'
            return url_base % self.playlist_slug


class MBCRadioProgramTable(object):
    default_imbc_table_path = path_join(abspath(getcwd()), 'imbc_table.csv')

    url = 'https://gist.githubusercontent.com/chwnam' + \
          '/29ddbf4900064f8ae9870df73f93530a/raw/5a5c2a8659b4b1a06a58b81201bbcfe6f15fddd3/imbc_table'

    table_path = abspath(getcwd())

    version = 0

    programs = None

    def __init__(self, table_path=None):
        self.table_path = table_path or self.default_imbc_table_path

        if not path_exists(self.table_path):
            self.download()

        self.load()

    def load(self):
        with open(self.table_path, 'r') as f:
            version_line = f.readline().strip()
            self.version = int(version_line.split(':')[1].strip())
            self.programs = []
            reader = csv_reader(f)
            for cols in reader:
                item = MBCRadioProgramItem()
                item.id = int(cols[0])
                item.channel = cols[2]
                item.start_time = cols[3]
                item.show_title = cols[4]
                item.homepage_slug = cols[5]
                item.playlist_slug = cols[6]
                self.programs.append(item)

        return self.version, self.programs

    def get_remote_version(self):
        conn = BasicConnector()
        content = conn.get(self.url)
        version_line = content.split('\n')[0].strip()
        return int(version_line.split(':')[1].strip())

    def download(self):
        conn = BasicConnector()
        content = conn.get(self.url)
        with open(self.table_path, 'w') as f:
            f.write(content)

    def update(self):
        remote_version = self.get_remote_version()
        if remote_version > self.version:
            self.download()
            self.load()


class MBCRadioPlaylistCrawler(object):
    date_expr = re_compile(r'^\d{4}-\d{2}-\d{2}$')

    def __init__(self, **kwargs):
        self.program_table = MBCRadioProgramTable(**kwargs)
        self.connector = BasicConnector(fallback_charset=['euc-kr', 'utf-8', ])

    def get_playlist(self, program_id, program_date=None):
        if not program_date:
            program_date = datetime.today().strftime('%Y-%m-%d')
        if not self.date_expr.match(program_date):
            return

        for program in self.program_table.programs:
            if program.id == program_id:
                view_url = self.get_view_url(program, program_date)
                return self.extract_playlist(view_url)

        return []

    def get_view_url(self, program: MBCRadioProgramItem, program_date: str):
        playlist_list_url = program.playlist_list_url
        if playlist_list_url:
            content = self.connector.get(
                url=playlist_list_url,
                params={
                    'txtstart': program_date,
                    'txtend': program_date
                }
            )
            parser = MBCRadioPlaylistListParser()
            parser.feed(content)
            if parser.rel_href:
                return program.url_prefix + parser.rel_href

    def extract_playlist(self, playlist_view_url):
        if playlist_view_url:
            content = self.connector.get(
                url=playlist_view_url
            )
            parser = MBCRadioPlaylistViewParser()
            parser.feed(content)
            return parser.playlist


class MBCRadioPlaylistListParser(object):
    def __init__(self):
        self.rel_href = ''

    def feed(self, content):
        soup = BeautifulSoup(markup=content, features='html.parser')
        try:
            self.rel_href = soup.find('table', class_='select_tb').tbody.find('a')['href']
        except AttributeError:
            pass
        except KeyError:
            pass


class MBCRadioPlaylistViewParser(object):
    def __init__(self):
        self.playlist = []

    def feed(self, content):
        soup = BeautifulSoup(markup=content, features='html.parser')
        playlist = []
        try:
            all_trs = soup.find('table', class_='list_tb').tbody.find_all('tr')
            for tr in all_trs:
                one_col = tr.th or tr.td
                if 'colspan' in one_col.attrs:
                    playlist.append(
                        {
                            'seq': None,
                            'title': one_col.text.strip(),
                            'artist': None,
                        }
                    )
                else:
                    tds = tr.find_all('td')
                    if len(tds) >= 5:
                        seq = tds[1].text.strip()
                        playlist.append(
                            {
                                'seq': int(seq) if seq.isnumeric() else seq,
                                'title': tds[2].text.strip(),
                                'artist': tds[3].text.strip(),
                            }
                        )
        except AttributeError:
            pass
        except KeyError:
            pass
        finally:
            self.playlist = playlist
