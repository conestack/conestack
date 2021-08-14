#!/bin/bash
set -e 

for file in .installed.cfg .mr.developer.cfg lib64; do
    if [ -e "$file" ]; then
        rm "$file"
    fi
done

for dir in lib include local bin share parts develop-eggs; do
    if [ -d "$dir" ]; then
        rm -r "$dir"
    fi
done

python3 -m venv .
./bin/pip install -r requirements.txt
./bin/buildout
