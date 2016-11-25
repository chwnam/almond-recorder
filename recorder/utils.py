from datetime import datetime, timedelta
from re import compile as re_compile

from os import (
    getcwd,
    listdir,
    stat,
    unlink,
    walk,
)

from os.path import (
    abspath,
    expanduser,
    expandvars,
    join as path_join,
    isfile,
    splitext,
)

from operator import itemgetter

from socket import (
    create_connection,
    gethostbyname,
)


class DirectoryCleaner(object):

    # NOTE: keep this order when using filter() method
    supported_orders = ('name', 'mtime', )

    def __init__(self):
        self._target_dir = ''
        self._target_ext = ''
        self._order = 'desc'
        self._order_by = 'mtime'
        self._reserve = 0
        self._limit = 0
        self._datetime_after = None
        self._datetime_before = None
        self._recursive = False
        self._pattern = r''
        self._pattern_flags = 0

        self.target = []

    def reset(self):
        """
        revert to default values
        """
        self._target_dir = ''
        self._target_ext = ''
        self._order = 'desc'
        self._order_by = 'mtime'
        self._reserve = 0
        self._limit = 0
        self._datetime_after = None
        self._datetime_before = None
        self._recursive = False
        self._pattern = r''
        self._pattern_flags = 0

        self.target = []

        return self

    def dir(self, directory: str):
        """
        set directory.
        default: current working directory
        """
        self._target_dir = directory
        return self

    def ext(self, extension: str):
        """
        set target extension
        extension string is encouraged to begin with a dot(.), but automatically appended if not.
        """
        if extension[0] != '.':
            self._target_ext = '.' + extension
        else:
            self._target_ext = extension
        return self

    def asc(self):
        """
        list files in ascending order
        """
        self._order = 'asc'
        return self

    def desc(self):
        """
        list files in descending order
        """
        self._order = 'desc'
        return self

    def order_by(self, value):
        """
        sets ordering criteria
        one of these:
         - name (file name)
         - mtime (modification time)
        """
        if value not in self.supported_orders:
            supported_text = ', '.join(['\'%x\'' % x for x in self.supported_orders])
            raise ValueError('invalid value \'%s\': supported: %s' % (value, supported_text))
        self._order_by = value
        return self

    def reserve(self, number):
        """
        only keep heading number of files in the list when clean() is called.
        """
        if self._limit:
            self._limit = 0
        self._reserve = number
        return self

    def limit(self, number):
        """
        only remove heading number of files the list when clean() is called.
        :param number:
        :return:
        """
        if self._reserve:
            self._reserve = 0
        self._limit = number
        return self

    def recursive(self, value: bool):
        """
        grab files in a recursive manner
        """
        self._recursive = value
        return self

    def before(self, datetime_value):
        """
        filter files older than the value
        :param datetime_value:
        :return:
        """
        self._datetime_before = datetime_value
        return self

    def after(self, datetime_value):
        """
        filter files newer than the value
        """
        self._datetime_after = datetime_value
        return self

    def all(self):
        """
        select all values.
        note that some values such as recursive are not considered!
        """
        self._target_ext = ''
        self._limit = 0
        self._reserve = 0
        self._datetime_after = None
        self._datetime_before = None
        self._pattern = ''
        self._pattern_flags = 0
        return self

    def pattern(self, value, flags=0):
        """
        you can also filter by a regular expression.
        """
        self._pattern = value
        self._pattern_flags = flags
        return self

    def files(self, exclude_mtime=False):
        """
        get filtered list
        """
        self.filter()
        if exclude_mtime:
            return [x[0] for x in self.target]
        return self.target

    def clean(self):
        """
        remove filtered files
        """
        for x in self.files():
            unlink(x)

    def filter(self):
        if self._limit and self._reserve:
            raise AttributeError('Setting both limit and reserve is too ambiguous.')

        if not self._target_dir:
            self._target_dir = abspath(getcwd())
        else:
            self._target_dir = abspath(expandvars(expanduser(self._target_dir)))

        filtered = self._grab_files(self._target_dir, self._recursive)

        if self._datetime_after:
            self._datetime_after = self._interpret_datetime(self._datetime_after)
            timestamp = self._datetime_after.timestamp()
            filtered = filter(lambda x: x[1] > timestamp, filtered)

        if self._datetime_before:
            self._datetime_before = self._interpret_datetime(self._datetime_before)
            timestamp = self._datetime_before.timestamp()
            filtered = filter(lambda x: x[1] < timestamp, filtered)

        if self._target_ext:
            filtered = filter(lambda x: splitext(x[0])[1] == self._target_ext, filtered)

        if self._pattern:
            r = re_compile(self._pattern, self._pattern_flags)
            filtered = filter(lambda x: r.search(x[0]) is not None, filtered)

        self.target = list(filtered)
        self.target.sort(
            key=itemgetter(self.supported_orders.index(self._order_by)),
            reverse=(self._order == 'desc')
        )

        if self._reserve:
            self.target = self.target[self._reserve:]

        elif self._limit:
            self.target = self.target[:self._limit]

    @staticmethod
    def _interpret_datetime(value):
        """
        value can be one of these:
          - str:       the value is parsed as datetime object. See patterns.
          - dict:      the value is used to create timedelta object.
          - timedelta: the value is subtracted from the current timestamp
          - datetime:  the value is used directly.
        :param value:
        :return:
        """
        obj = None
        if isinstance(value, str):
            patterns = [
                '%Y-%m-%d %H:%M:%S'  # 2016-11-24 20:50:34
                '%Y/%m/%d %H:%M:%S'  # 2016-11-24 20:50:34
                '%Y%m%d %H%M%S'      # 20161124 205034
                '%Y%m%d%H%M%S'       # 20161124205034
            ]
            try:
                for pattern in patterns:
                    obj = datetime.strptime(value, pattern)
            except ValueError:
                pass
        elif isinstance(value, dict):
            obj = datetime.utcnow() - timedelta(**value)
        elif isinstance(value, timedelta):
            obj = datetime.utcnow() - value
        elif isinstance(value, datetime):
            obj = value

        if obj is None:
            raise ValueError()

        return obj

    @staticmethod
    def _grab_files(target_dir: str, recursive: bool):
        """
        crawl files from target directory.
        all files are abstract.
        :param target_dir:
        :param recursive:
        :return:
        """
        target = []
        if recursive:
            for dir_path, _, file_names in walk(target_dir):
                for file_name in file_names:
                    # NOTE: tuple's order of item must match supported_orders
                    path = abspath(path_join(dir_path, file_name))
                    mtime = stat(path).st_mtime
                    target.append((path, mtime))
        else:
            for item in listdir(target_dir):
                path = abspath(path_join(target_dir, item))
                if isfile(path):
                    mtime = stat(path).st_mtime
                    target.append((path, mtime))
        return target


def check_connection(remote_server=None, timeout=2):
    if not remote_server:
        remote_server = 'www.google.com'

    # noinspection PyBroadException
    try:
        host = gethostbyname(remote_server)
        conn = create_connection((host, 80), timeout=timeout)
        conn.close()
    except:
        return False

    return True
