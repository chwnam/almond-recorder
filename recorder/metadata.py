from json import loads as json_loads


class FFMpegStreamInfo(object):
    index = None
    bitrate = None
    channel_layout = None
    channels = None
    codec_name = None
    sample_rate = None
    duration = None

    def __init__(self, **kwargs):
        self.index = kwargs.get('index')
        self.bitrate = kwargs.get('bit_rate')
        self.channel_layout = kwargs.get('channel_layout')
        self.codec_name = kwargs.get('codec_name')
        self.sample_rate = kwargs.get('sample_rate')
        self.duration = kwargs.get('duration_ts')


class FFMpegMetadata(object):
    album = ''
    album_artist = ''
    author = ''
    copyright = ''
    description = ''
    genre = ''
    keywords = ''
    rating = ''
    title = ''

    def __init__(self, **kwargs):
        tags = kwargs.get('tags', {})
        self.album = tags.get('album', '')
        self.album_artist = tags.get('album_artist', '')
        self.author = tags.get('author', '')
        self.copyright = tags.get('copyright', '')
        self.description = tags.get('description', '')
        self.genre = tags.get('genre', '')
        self.keywords = tags.get('keywords', '')
        self.rating = tags.get('rating', '')
        self.title = tags.get('title', '')

    def items(self):
        return self.__dict__.items()

    def __iter__(self):
        return self.__dict__.__iter__()


class FFProbeResult(object):

    streams = []
    metadata = None

    def __init__(self, ffprobe_output):
        if isinstance(ffprobe_output, str):
            probed = json_loads(ffprobe_output)
        elif isinstance(ffprobe_output, dict):
            probed = ffprobe_output
        else:
            probed = {}

        if 'streams' in probed and isinstance(probed['streams'], list):
            self.streams = [FFMpegStreamInfo(**kwargs) for kwargs in probed['streams'] if isinstance(kwargs, dict)]

        if 'format' in probed and isinstance(probed['format'], dict):
            kwargs = probed['format']
            self.metadata = FFMpegMetadata(**kwargs)
