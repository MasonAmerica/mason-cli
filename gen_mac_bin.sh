#!/bin/sh -e

echo "__version__ = '$(cat VERSION)'" > masonlib/version.py
pip3 install .
pyinstaller masonlib/mason.py --onefile \
  --add-data "$(pip3 show pyaxmlparser | grep Location | cut -c11-)/pyaxmlparser/resources/public.xml:pyaxmlparser/resources" \
  --add-data VERSION:.
