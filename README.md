Almond Recorder
===============

An easy, NAS friendly internet radio recorder.

Currently it supports [MBC](http://www.imbc.com) only, and CLI interface is provided only.

Python 3.5+

Sample Usage
------------
FM4U channel recording (until Ctrl+C pressed) 
```
python mbc_radio.py --channel mfm --output ~/output.m4a
```


Standard channel recording for an hour
```
python mbc_radio.py --channel sfm --duration 3600 --ouput ~/radio_show.m4a
```


Adding metadata after recording
```
python mbc_radio.py --channel mfm --duration 3600 --ouput ~/radio_show.m4a --metadata artist=<artist> album=<album> title=<title> ...
```


Playlist acquisition: playlist is written at 'comment' tag.
```
python mbc_playlist -u # only once. "imbc_table.csv" is fetched.
python mbc_playlist -l # identify your radio show's id

python mbc_playlist -i <input> -p <ID> -d yyyy-mm-dd -o <output> # save as output file
python mbc_playlist -i <input> -p <ID> -d yyyy-mm-dd -r          # input file is replaced
```
