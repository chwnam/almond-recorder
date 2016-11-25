from os import (
    close as os_close,
    unlink
)

from tempfile import mkstemp, gettempdir

from .backends import MPlayer, FFMpeg, FFMpegMetadata
from .exceptions import AlreadyRecording


class AudioStreamRecorder(object):

    def __init__(self, **kwargs):
        """
        """
        self.backend = MPlayer(**kwargs)
        self.work_path = kwargs.pop('work_path', gettempdir())

    @property
    def is_recording(self):
        return self.backend.is_recording

    @property
    def is_stopped(self):
        return self.backend.is_stopped

    def record(self, url, duration, destination=None):
        if self.backend.is_recording:
            return

        if destination is None:
            temp_fd, destination = mkstemp(dir=self.work_path)
            os_close(temp_fd)

        self.backend.record(url, destination).wait(duration).terminate()

        return destination


class MetadataPostProcess(object):

    def __init__(self, **kwargs):
        self.ffmpeg = FFMpeg(**kwargs)

    def process(self, input_path: str, metadata: FFMpegMetadata, output_path: str):
        if self.ffmpeg.insert_metadata(input_path=input_path, metadata=metadata, output_path=output_path) == 0:
            unlink(input_path)
