from datetime import datetime, timedelta

from os import (
    getcwd,
    listdir,
    stat,
    walk,
)

from os.path import (
    abspath,
    join as path_join,
    isfile,
    splitext,
)

from operator import itemgetter


class DirectoryCleaner(object):

    supported_orders =  ('mtime', 'name')

    def __init__(self):
        self.target_dir = ''
        self.target_ext = ''
        self.order = 'desc'
        self.order_by = 'mtime'
        self.reserve = 0
        self.limit = 0
        self.datetime_after = None
        self.datetime_before = None
        self.recursive = False

        self.target = []

    def dir(self, directory: str):
        self.target_dir = directory
        return self

    def ext(self, extension: str):
        if extension[0] != '.':
            self.target_ext = '.' + extension
        else:
            self.target_ext = extension
        return self

    def asc(self):
        self.order = 'asc'
        return self

    def desc(self):
        self.order = 'desc'
        return self

    def order_by(self, value):
        if value not in self.supported_orders:
            supported_text = ', '.join(['\'%x\'' % x for x in self.supported_orders])
            raise ValueError('invalid value \'%s\': supported: %s' % (value, supported_text))
        self.order_by = value
        return self

    def reserve(self, number):
        self.reserve = number
        return self

    def limit(self, number):
        self.limit = number
        return self

    def recursive(self, value: bool):
        self.recursive = value
        return self

    def before(self, datetime_value):
        self.datetime_before = datetime_value
        return self

    def after(self, datetime_value):
        self.datetime_after = datetime_value
        return self

    def files(self):
        self.filter()
        return self.target

    def clean(self):
        pass

    def filter(self):

        if self.limit and self.reserve:
            raise AttributeError('Setting bot limit and reserve is too ambiguous.')

        if not self.target_dir:
            self.target_dir = abspath(getcwd())
        else:
            self.target_dir = abs(self.target_dir)

        self.target = self._grab_files(self.target_dir, self.recursive)

        if self.datetime_after:
            self.datetime_after = self._interpret_datetime(self.datetime_after)
            timestamp = self.datetime_after.timestamp()
            filtered = filter(lambda x: x[1] > timestamp, self.target)
            self.target = list(filtered)

        if self.datetime_before:
            self.datetime_before = self._interpret_datetime(self.datetime_before)
            timestamp = self.datetime_after.timestamp()
            filtered = filter(lambda x: x[1] < timestamp, self.target)
            self.target = list(filtered)

        if self.target_ext:
            filtered = filter(lambda x: splitext(x[0])[1] == self.target_ext, self.target)
            self.target = list(filtered)

        self.target.sort(
            key=itemgetter(self.supported_orders.index(self.order)),
            reverse=(self.order_by == 'desc')
        )

        if self.reserve:
            self.target = self.target[self.reserve:]
        elif self.limit:
            self.limit = self.target[:self.limit]

    @staticmethod
    def _interpret_datetime(value):
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
        target = []
        if recursive:
            for dir_path, _, file_names in walk(target_dir):
                for file_name in file_names:
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
