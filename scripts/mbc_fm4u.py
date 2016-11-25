from os.path import expanduser
from recorder import urls
from recorder import (
    AudioStreamRecorder,
    MetadataPostProcess
)
from recorder.metadata import FFMpegMetadata


def record_mbc_fm4u(duration: int, output_path: str, work_path: str):

    url = urls.MbcRadioUrl().fm4u()

    recorder = AudioStreamRecorder(work_path=work_path)
    record_file = recorder.record(url=url, duration=duration)

    metadata = FFMpegMetadata()
    metadata.album = '테스트 앨범'
    metadata.artist = 'FM4U'
    metadata.album_artist = 'FM4U'
    metadata.author = 'MBC'
    metadata.title = '테스트 녹음'

    metadata_process = MetadataPostProcess()
    metadata_process.process(input_path=record_file, metadata=metadata, output_path=output_path)


def record_mbc_fm4u_test():

    duration = 10
    output_path = 'out.m4a'
    work_path = expanduser('~')

    record_mbc_fm4u(duration=duration, output_path=output_path, work_path=work_path)


if __name__ == '__main__':
    record_mbc_fm4u_test()
