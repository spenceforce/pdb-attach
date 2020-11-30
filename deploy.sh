#!/usr/bin/env bash
set -e

npx standard-version
export SKIP_GIT_SDIST=1
export SKIP_GENERATE_AUTHORS=1
export SKIP_WRITE_GIT_CHANGELOG=1
export SKIP_GENERATE_RENO=1
python setup.py sdist bdist_wheel
twine upload dist/*
