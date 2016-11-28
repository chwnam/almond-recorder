from os import (
    close as os_close,
    unlink
)

from tempfile import mkstemp, gettempdir

from .backends import MPlayer, FFMpeg, FFMpegMetadata
from .exceptions import InvalidChannelException
from .urls import MbcRadioUrl


class AudioStreamRecorder(object):

    def __init__(self, **kwargs):
        """
        Keywords
        --------
            work_path: recording path. Defaults to the system's temporary directory.
        """
        self.backend = MPlayer(**kwargs)
        self.work_path = kwargs.pop('work_path', gettempdir())

    @property
    def is_recording(self):
        return self.backend.is_recording

    @property
    def is_stopped(self):
        return self.backend.is_stopped

    def record(self, url, duration=0, destination=None):
        if self.backend.is_recording:
            return

        if destination is None:
            temp_fd, destination = mkstemp(dir=self.work_path)
            os_close(temp_fd)

        try:
            if duration == 0:
                self.backend.record(url, destination)
                while True:
                    self.backend.wait(10)
            else:
                self.backend.record(url, destination).wait(duration)
        except KeyboardInterrupt:
            pass
        finally:
            self.backend.stop()

        return destination


class MetadataPostProcess(object):

    def __init__(self, **kwargs):
        self.ffmpeg = FFMpeg(**kwargs)

    def process(self, input_path: str, metadata, output_path: str):
        if self.ffmpeg.insert_metadata(input_path=input_path, metadata=metadata, output_path=output_path) == 0:
            unlink(input_path)


class MBCRadioRecorder(object):

    def __init__(self, **kwargs):
        self.stream_recorder = AudioStreamRecorder(**kwargs)
        self.metadata_process = MetadataPostProcess()

    def record_now(self, channel: str, duration: int, output: str, metadata: dict=None):
        """
        Record now
        :param channel:
        :param duration:
        :param output:
        :param metadata:
        :return:
        """
        if duration <= 0:
            return

        metadata = metadata or {}
        temp = self.stream_recorder.record(url=self.get_url(channel), duration=duration)

        if metadata:
            self.metadata_process.process(
                input_path=temp,
                metadata=FFMpegMetadata(**metadata),
                output_path=output
            )
        else:
            # just rename temp
            pass

    @staticmethod
    def get_url(channel):

        url = MbcRadioUrl()

        if channel in url.channels:
            func = getattr(url, channel)
            return func()

        channels = ', '.join(["'%s'" % x for x in url.channels])
        raise InvalidChannelException(
            'Channel \'%s\' is not available. Please choose one of these: %s' % channels
        )
