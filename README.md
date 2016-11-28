Almond Recorder
===============

An easy internet radio recorder for iMBC.

Python 3.5+

Usage
------------
FM4U channel recording (until Ctrl+C pressed) 
```
python imbc_radio.py --channel mfm --output ~/output.m4a
```


Standard channel recording for an hour
```
python imbc_radio.py --channel sfm --duration 3600 --ouput ~/radio_show.m4a
```


Adding metadata after recording
```
python imbc_radio.py --channel mfm --duration 3600 --ouput ~/radio_show.m4a --metadata artist=<artist> album=<album> title=<title> ...
```
