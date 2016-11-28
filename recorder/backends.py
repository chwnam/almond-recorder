from subprocess import Popen, PIPE, TimeoutExpired, STDOUT, DEVNULL
from sys import stdout
from time import sleep

from .metadata import FFProbeResult, FFMpegMetadata

FFMPEG_PATH = '/usr/bin/ffmpeg'

FFPROBE_PATH = '/usr/bin/ffprobe'

MPLAYER_PATH = '/usr/bin/mplayer'

MPLAYER_CACHE_SIZE = 8192


class PopenBasedBackend(object):

    def __init__(self, **kwargs):
        """
        Keywords
        --------
         - timeout: timeout value when com()
        """
        self.encoding = kwargs.pop('encoding', stdout.encoding)
        self.stdout_str = ''
        self.stderr_str = ''
        self.return_val = None
        self.process = None

    @property
    def is_working(self):
        return isinstance(self.process, Popen)

    @property
    def is_stopped(self):
        return self.process is None

    @property
    def pid(self):
        if self.is_working:
            return self.process.pid

    def start(self, command, _stdin=PIPE, _stdout=PIPE, _stderr=PIPE):
        if self.is_stopped:
            self.process = Popen(command, stdin=_stdin, stdout=_stdout, stderr=_stderr)
        return self

    def stop(self, timeout=2):
        if self.is_working:
            self.process.terminate()
            return self.communicate(timeout=timeout)

    def communicate(self, timeout=None):
        try:
            self.stdout_str, self.stderr_str = self.process.communicate(timeout=timeout)
        except TimeoutExpired:
            self.process.kill()
            self.stdout_str, self.stderr_str = self.process.communicate()
        finally:
            if self.stdout_str:
                self.stdout_str = self.stdout_str.decode(self.encoding)
            if self.stderr_str:
                self.stderr_str = self.stderr_str.decode(self.encoding)
            self.return_val = self.process.returncode
            self.process = None
            return self.return_val


class MPlayer(PopenBasedBackend):
    def __init__(self, **kwargs):
        """
        :param kwargs:
        """
        super(MPlayer, self).__init__(**kwargs)
        self.mplayer = kwargs.pop('mplayer_path', MPLAYER_PATH)
        self.cache_size = kwargs.pop('mplayer_cache_size', MPLAYER_CACHE_SIZE)

    @property
    def is_recording(self):
        return self.is_working

    def record(self, source_path: str, dump_file: str):
        command = [
            self.mplayer,
            source_path,
            '-cache', '%d' % self.cache_size,
            '-dumpstream',
            '-dumpfile', '%s' % dump_file,
            '-quiet',
            '-really-quiet'
        ]

        return self.start(command, _stdout=DEVNULL, _stderr=STDOUT)

    def wait(self, duration):
        if duration:
            sleep(duration)
        return self


class FFProbe(PopenBasedBackend):
    def __init__(self, **kwargs):
        super(FFProbe, self).__init__(**kwargs)
        self.ffprobe = kwargs.pop('ffprobe_path', FFPROBE_PATH)

    def probe(self, path):
        command = [
            self.ffprobe,
            '-hide_banner',
            '-loglevel', 'panic',
            '-print_format', 'json',
            '-show_streams',
            '-show_format',
            path
        ]
        self.start(command).communicate()

        return FFProbeResult(self.stdout_str)


class FFMpeg(PopenBasedBackend):
    def __init__(self, **kwargs):
        super(FFMpeg, self).__init__(**kwargs)
        self.ffmpeg = kwargs.pop('ffmpeg_path', FFMPEG_PATH)

    def insert_metadata(self, input_path: str, metadata, output_path: str):

        if isinstance(metadata, dict):
            mo = FFMpegMetadata(**metadata)
        elif isinstance(metadata, FFMpegMetadata):
            mo = metadata
        else:
            mo = {}

        command = [
            self.ffmpeg,
            '-hide_banner',
            '-y',
            '-loglevel', 'panic',
            '-i', input_path
        ]

        for key, val in mo.items():
            if val:
                command += ['-metadata', ('%s=%s' % (key, val))]

        command += [
            '-codec', 'copy',
            output_path
        ]

        return self.start(command).communicate()
