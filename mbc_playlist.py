from argparse import ArgumentParser
from hashlib import md5
from os import (
    rename,
    stat,
    unlink,
)

from os.path import (
    exists as path_exists,
    splitext,
)

from sys import stdout, stderr
from time import time
from random import random

from recorder.playlist import MBCRadioPlaylistCrawler
from recorder.backends import FFMpeg


class MBCPlaylist(object):

    def __init__(self, table_path=None, ffmpeg_path=None):
        self.crawler = MBCRadioPlaylistCrawler(table_path=table_path)
        self.ffmpeg = FFMpeg(ffmpeg_path=ffmpeg_path)

    def list_programs(self, out=stdout):
        print('VERSION:', self.crawler.program_table.version, file=out)
        print(file=out)
        print('ID\tCHANNEL\tPLAYLIST_SLUG\tHOUR\tTITLE', file=out)
        print('-' * 80, file=out)
        for program in self.crawler.program_table.programs:
            print(
                '{}\t{}\t{}\t{}\t{}'.format(
                    program.id,
                    program.channel,
                    program.playlist_slug or '\t',
                    program.start_time,
                    program.show_title
                ),
                file=out
            )

    def update_table(self):
        self.crawler.program_table.update()

    def version(self, out=stdout):
        print(self.crawler.program_table.version, file=out)

    def insert_playlist(self, program_id, program_date, input_path, output_path):
        playlist = self.crawler.get_playlist(program_id, program_date)
        return self.ffmpeg.insert_metadata(
            input_path=input_path,
            output_path=output_path,
            metadata={
                'description': self.format_text(playlist)
            }
        )

    @staticmethod
    def format_text(playlist):
        last_seq = playlist[-1]['seq'] if playlist else 0
        lines = [
            '#%02d/%02d %s - %s' % (item['seq'], last_seq, item['artist'], item['title'])
            if item['seq'] else item['title']
            for item in playlist
        ]
        return '\n'.join(lines)


class MBCPlaylistScript(object):

    def __init__(self):
        self.parser = ArgumentParser()

    def parse(self):
        self.parser.add_argument('-i', '--input')
        self.parser.add_argument('-o', '--output')
        self.parser.add_argument('-r', '--replace', action='store_true', default=False)
        self.parser.add_argument('-p', '--program-id', type=int)
        self.parser.add_argument('-d', '--playlist-date')
        self.parser.add_argument('-t', '--table-path', default=None)
        self.parser.add_argument('--ffmpeg-path', default=None)

        # misc functions
        self.parser.add_argument('--print-only', action='store_true', default=False)
        self.parser.add_argument('-l', '--list-programs', action='store_true', default=False)
        self.parser.add_argument('-u', '--update-table', action='store_true', default=False)
        self.parser.add_argument('-v', '--version', action='store_true', default=False)

        return self.parser.parse_args()

    def run(self):
        args = self.parse()
        playlist = MBCPlaylist(
            table_path=args.table_path,
            ffmpeg_path=args.ffmpeg_path
        )

        if args.list_programs:
            playlist.list_programs()

        elif args.update_table:
            playlist.update_table()

        elif args.version:
            playlist.version()

        else:
            if args.print_only:
                if not self._check_program_id(args, stderr):
                    return
                elif not self._check_playlist_date(args, playlist, stderr):
                    return
                print(
                    playlist.format_text(playlist.crawler.get_playlist(args.program_id, args.playlist_date)),
                    file=stdout
                )
            else:
                if not self._check_program_id(args, stderr):
                    return
                elif not args.replace and not args.output:
                    print('--replace is not set. --output parameter is required', file=stderr)
                    return
                elif not args.program_id:
                    print('--program-id parameter is missing', file=stderr)
                    return
                elif not self._check_playlist_date(args, playlist, stderr):
                    return

                if args.replace:
                    output_path = self._get_temp_output_path(args.input)
                    return_val = playlist.insert_playlist(args.program_id, args.playlist_date, args.input, output_path)
                    if return_val == 0 and path_exists(output_path):
                        # also deliberately check two file's size.
                        # output file should be equal or greater than input
                        input_stat = stat(args.input)
                        output_stat = stat(output_path)
                        if output_stat.st_size >= input_stat.st_size:
                            unlink(args.input)
                            rename(output_path, args.input)
                else:
                    playlist.insert_playlist(args.program_id, args.playlist_date, args.input, args.output)

    @staticmethod
    def _check_program_id(args, file):
        if not args.program_id:
            print('--program-id parameter is missing', file=file)
            return False
        return True

    @staticmethod
    def _check_playlist_date(args, playlist, file):
        if not args.playlist_date or not playlist.crawler.date_expr.match(args.playlist_date):
            print(
                '--playlist-date parameter is missing or invalid. Format like \'%s\'' % (
                    '-'.join(['y' * 4, 'm' * 2, 'd' * 2])
                ),
                file=file
            )
            return False
        return True

    @staticmethod
    def _get_temp_output_path(input_path):
        split = splitext(input_path)
        random_text = str(time()) + str(random())
        m = md5()
        m.update(random_text.encode('utf-8'))
        return split[0] + '_' + m.hexdigest() + split[1]

if __name__ == '__main__':
    MBCPlaylistScript().run()
