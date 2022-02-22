#!/bin/bash
#
# Install development environment.

set -e

OPENLDAP="$(realpath openldap)"

function create_venv {
    python3 -m venv .
    ./bin/pip install -U \
        pip \
        setuptools \
        wheel \
        mxdev \
        zope.testrunner \
        plone.testing
}

function install_python_ldap {
    sudo apt-get build-dep python-ldap
    ./bin/pip install \
        --global-option=build_ext \
        --global-option="-I$OPENLDAP/include" \
        --global-option="-L$OPENLDAP/lib" \
        --global-option="-R$OPENLDAP/lib" \
        python-ldap
}

function install_packages {
    touch requirements.txt
    ./bin/mxdev -c sources.ini
    ./bin/pip install -r requirements-mxdev.txt
}

./scripts/clean.sh
./scripts/openldap.sh

create_venv
install_python_ldap
install_packages

exit 0
