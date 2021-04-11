#!/usr/bin/env bash
set -e

npx standard-version
rm -rf build dist pdb_attach.egg-info
python setup.py sdist bdist_wheel
twine upload dist/*
