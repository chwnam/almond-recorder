"""
cleaner = DirectoryCleaner()
cleaner.set_directory('somewhere').clean_older_than(
    seconds=
    minutes=
    hours=
    days=2,
    months=
    years=
)

# 모든 파일을 지움
cleaner.dir('somewhere').all().clean()

# 확장자 m4a를 지움
cleaner.dir('somewhere').ext('.m4a').clean()

# 현재로부터 일정 기간 이전 파일을 지움
cleaner.dir('somewhere').before(...).clean()

# 현재로부터 일정 기간 이후 파일을 지움
cleaner.dir('somewhere').after(...).clean()

# 가장 오래된 파일 3개만 남기고 지움 (정렬된 목록의 처음 3개만 남기므로)
cleaner.dir('somewhere').asc().reserve(3).clean()

# 가장 최근 파일 3개만 남기고 지움
cleaner.dir('somewhere').desc().reserve(3).clean()

# 디렉토리의 파일 3개만 지운다.
# 기본은 desc 정렬이므로 가장 최신 3개가 삭제됨
cleaner.dir('somewhere').limit(3).clean()

# reserve, limit 을 한 번에 동시에 쓸 수는 없다.
# 각각을 해제하는 방법: 인자로 0을 넣으면 된다.

# 가장 최신 파일의 3개만 삭제한다.
cleaner.dir('somewhere').desc().limit(3).clean()

# 파일 목록을 검색
cleaner.dir('somewhere').files()

# 하위 디렉토리도 검색 (somewhere 디렉토리는 지우지 않는다)
cleaner.dir('somewhere').recursive(True).clean()

# 해당 기간 이전의 .m4a 파일을 지우는데, 가장 오래된 파일 3개는 남긴다.
cleaner.dir('somewhere').before(...).asc().reserve(3)

# 2주 전 파일을 지우는데, dir_a, dir_b, dir_c 디렉토리에 같이 작업.
# 단, 모두 지우지는 말고 최신 3는 남겨두자.
cleaner.before(days=14).desc().reserve(3)
    .dir('dir_a').clean()
    .dir('dir_b').clean()
    .dir('dir_c').clean()
"""
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
