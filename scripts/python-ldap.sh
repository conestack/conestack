#!/bin/bash
#
# Install python-ldap

set -e

openldap="$(realpath openldap)"

./bin/pip install \
    --no-use-pep517 \
    --global-option=build_ext \
    --global-option="-I$openldap/include" \
    --global-option="-L$openldap/lib" \
    --global-option="-R$openldap/lib" \
    python-ldap

exit 0
