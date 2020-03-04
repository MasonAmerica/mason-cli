#!/bin/sh -e

echo "__version__ = '$(cat VERSION)'" > cli/version.py
wine pip install windows-curses
wine pip install .
wine pyinstaller cli/mason.py --onefile \
  --hidden-import='pkg_resources.py2_warn' \
  --add-data "C:\\Python37\\Lib\\site-packages\\pyaxmlparser\\resources\\public.xml;pyaxmlparser\\resources" \
  --add-data "VERSION;." \
  --add-data "openssl-win;cli/internal/models" \
  --icon m.ico
