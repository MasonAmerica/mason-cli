#!/bin/sh -e

pip3 install .
pyinstaller mason.py --onefile \
  --add-data "$(pip3 show pyaxmlparser | grep Location | cut -c11-)/pyaxmlparser/resources/public.xml:pyaxmlparser/resources" \
  --add-data VERSION:.
