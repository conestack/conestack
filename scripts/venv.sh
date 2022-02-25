#!/bin/bash
#
# Install virtual environment environment.

set -e

function create_venv {
    python3 -m venv .
    ./bin/pip install -U \
        pip \
        setuptools \
        wheel \
        mxdev
}

function install_python_ldap {
    local openldap="$(realpath openldap)"
    ./bin/pip install \
        --no-use-pep517 \
        --global-option=build_ext \
        --global-option="-I$openldap/include" \
        --global-option="-L$openldap/lib" \
        --global-option="-R$openldap/lib" \
        python-ldap
}

function install_packages {
    touch requirements.txt
    ./bin/mxdev -c sources.ini
    ./bin/pip install -r requirements-mxdev.txt
}

create_venv
install_python_ldap
install_packages
