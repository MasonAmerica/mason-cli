#!/bin/bash -ex

echo "__version__ = '$(cat VERSION)'" > cli/version.py
pip3 install .
pyinstaller cli/mason.py --onefile \
  --add-data "$(pip3 show pyaxmlparser | grep Location | cut -c11-)/pyaxmlparser/resources/public.xml:pyaxmlparser/resources" \
  --add-data VERSION:.

./dist/mason version
./dist/mason --id-token a --access-token b register --dry-run apk tests/res/v1.apk
