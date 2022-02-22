#!/bin/bash
#
# Download and build openldap

set -e

VERSION="2.4.59"
URL="https://www.openldap.org/software/download/OpenLDAP/openldap-release/"

function install_dependencies {
    sudo apt-get install -y \
        build-essential \
        curl \
        libsasl2-dev \
        libssl-dev \
        libdb-dev \
        libltdl-dev
}

function get_openldap {
    rm -rf openldap
    curl -o openldap-$VERSION.tgz $URL/openldap-$VERSION.tgz
    tar xf openldap-$VERSION.tgz
    rm openldap-$VERSION.tgz
    mv openldap-$VERSION openldap
}

function build_openldap {
    pushd openldap >/dev/null 2>&1
    ./configure \
        --with-tls \
        --enable-slapd=yes \
        --enable-overlays \
        --prefix=$(realpath .)
    make clean
    make depend
    make -j4
    make install
    popd >/dev/null 2>&1
}

install_dependencies
get_openldap
build_openldap

exit 0
