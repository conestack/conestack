#!/bin/bash
#
# Clean development environment.

to_remove=(
    .coverage
    bin
    constraints-mxdev.txt
    docs/html
    htmlcov
    include
    lib64
    lib
    openldap
    pyvenv.cfg
    requirements-mxdev.txt
    share
)

for item in "${to_remove[@]}"; do
    if [ -e "$item" ]; then
        rm -r "$item"
    fi
done
