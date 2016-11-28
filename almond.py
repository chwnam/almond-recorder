from argparse import (
    ArgumentParser,
    ArgumentDefaultsHelpFormatter,
)


class AlmondArgumentParser(object):

    def __init__(self):
        self.parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
        self.build_parser()

    def build_parser(self):
        pass

    def parse_args(self):
        return self.parser.parse_args(namespace='almond')


class AlmondRecorder(object):

    def __init__(self):
        self.parser = AlmondArgumentParser()

    def run(self):
        args = self.parser.parse_args()


if __name__ == '__main__':

    recorder = AlmondRecorder()
    recorder.run()
