#!/bin/bash -ex

echo "__version__ = '$(cat VERSION)'" > cli/version.py
wine pip install windows-curses
wine pip install .
wine pyinstaller cli/mason.py --onefile \
  --hidden-import='pkg_resources.py2_warn' \
  --add-data "C:\\Python37\\Lib\\site-packages\\pyaxmlparser\\resources\\public.xml;pyaxmlparser\\resources" \
  --add-data "VERSION;." \
  --icon m.ico

wine dist/mason.exe version
wine dist/mason.exe --id-token a --access-token b register --dry-run apk tests/res/v1.apk
