#!/bin/bash
#
# Install development environment.

./scripts/clean.sh

python3 -m venv .

./bin/pip install mxdev
./bin/mxdev -c sources.ini
./bin/pip install -r requirements-mxdev.txt
