#!/bin/bash
#
# Cleanup and build development environment.

set -e

./scripts/clean.sh
./scripts/openldap.sh
./scripts/venv.sh
