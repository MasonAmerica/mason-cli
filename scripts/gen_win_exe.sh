#!/bin/sh -e

echo "__version__ = '$(cat VERSION)'" > cli/version.py
PYTHONHASHSEED=8 wine ~/.wine/drive_c/Python37/Scripts/pip.exe install windows-curses
PYTHONHASHSEED=8 wine ~/.wine/drive_c/Python37/Scripts/pip.exe install .
PYTHONHASHSEED=8 wine ~/.wine/drive_c/Python37/Scripts/pyinstaller.exe cli/mason.py --onefile \
  --hidden-import='pkg_resources.py2_warn' \
  --add-data "C:\\Python37\\Lib\\site-packages\\pyaxmlparser\\resources\\public.xml;pyaxmlparser\\resources" \
  --add-data "VERSION;." \
  --add-data "openssl-win;cli/internal/models" \
  --icon m.ico
