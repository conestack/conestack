#!/bin/bash
#
# Install development environment.

./scripts/clean.sh

# apt-get build-dep python-ldap

touch requirements.txt

python3 -m venv .

./bin/pip install -U pip setuptools wheel mxdev
./bin/mxdev -c sources.ini
./bin/pip install -r requirements-mxdev.txt
