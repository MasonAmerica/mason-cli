#!/bin/sh -e

echo "__version__ = '$(cat VERSION)'" > cli/version.py
pip3 install .
pyinstaller cli/mason.py \
  --add-data "$(pip3 show pyaxmlparser | grep Location | cut -c11-)/pyaxmlparser/resources/public.xml:pyaxmlparser/resources" \
  --add-data VERSION:.

(cd dist && ./mason/mason version)
