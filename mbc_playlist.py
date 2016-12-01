from recorder.playlist import MBCRadioPlaylistCrawler


if __name__ == '__main__':

    crawler = MBCRadioPlaylistCrawler(table_path=None)
    print('VERSION:', crawler.program_table.version)
    print()
    print('ID\tCHANNEL\tPLAYLIST_SLUG\tHOUR\tTITLE')
    print('-' * 80)
    for program in crawler.program_table.programs:
        print(
            '{}\t{}\t{}\t{}\t{}'.format(
                program.id,
                program.channel,
                program.playlist_slug or '\t',
                program.start_time,
                program.show_title
            )
        )

    # 정지영, 2016년 11월 2일 선곡표
    playlist = crawler.get_playlist(7, '2016-11-01')
    last_seq = playlist[-1]['seq'] if playlist else 0
    for item in playlist:
        if item['seq']:
            print('#%02d/%02d %s - %s' % (item['seq'], last_seq, item['artist'], item['title']))
        else:
            print(item['title'])
