from argparse import ArgumentParser

from recorder import AudioStreamRecorder, MetadataPostProcess
from recorder.urls import MbcRadioUrl


class MBCRecorder(object):

    def __init__(self, **kwargs):
        self.stream_Recorder = AudioStreamRecorder(**kwargs)
        self.post_process = MetadataPostProcess(**kwargs)
        self.radio_url = MbcRadioUrl()

    def record(self, channel: str, duration: int, output_path: str, metadata: dict=None):
        if channel not in MbcRadioUrl.channels:
            raise AttributeError(
                'Invalid channel: \'%s\'. Supported channels are %s' % (channel, ', '.join(MbcRadioUrl.channels))
            )

        url = getattr(self.radio_url, channel)()

        if not metadata:
            self.stream_Recorder.record(url=url, duration=duration, destination=output_path)
        else:
            temporary_path = self.stream_Recorder.record(url=url, duration=duration)
            self.post_process.process(temporary_path, metadata=metadata, output_path=output_path)


class MBCRecorderScript(object):

    def __init__(self):
        self.parser = ArgumentParser()
        self.build_parser()

    def build_parser(self):
        self.parser.add_argument('-c', '--channel', required=True, choices=MbcRadioUrl.channels)
        self.parser.add_argument('-o', '--output', required=True)
        self.parser.add_argument('-d', '--duration', type=int, default=0)
        self.parser.add_argument('-m', '--metadata', nargs='*', default=[])

        # ffmpeg argument
        self.parser.add_argument('--ffmpeg-path', nargs='?')

        # MPlayer arguments
        self.parser.add_argument('--mplayer-path', nargs='?')
        self.parser.add_argument('--mplayer-cache-size', nargs='?', type=int)

        # AudioStreamRecorder argument
        self.parser.add_argument('--work-path', nargs='?')

    def run(self):
        args = vars(self.parser.parse_args())

        # extract kwargs
        kwargs = {}
        kws = ('ffmpeg_path', 'mplayer_path', 'mplayer_cache_size', 'work_path')
        for kw in kws:
            if args[kw]:
                kwargs[kw] = args[kw]

        # metadata values conversion
        metadata_dict = {}
        for item in args['metadata']:
            idx = item.find('=')
            if idx > -1:
                key = item[:idx].strip()
                val = item[idx+1:].strip()
                metadata_dict[key] = val

        recorder = MBCRecorder(**kwargs)
        recorder.record(
            channel=args['channel'],
            duration=args['duration'],
            output_path=args['output'],
            metadata=metadata_dict,
        )


if __name__ == '__main__':
    script = MBCRecorderScript()
    script.run()
