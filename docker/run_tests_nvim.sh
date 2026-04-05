#!/usr/bin/env bash

set -e -o pipefail

PYTHON_CMD="$(which python)"
VIM="/usr/local/bin/nvim"
PYTHON_VERSION=$($PYTHON_CMD -c 'import sys;print(sys.version.split()[0])')
echo "Using python from: $PYTHON_CMD Version: $PYTHON_VERSION"
echo "Using nvim from: $VIM"
$VIM --version | head -n 3

set -x

tmux new -d -s vim

stdbuf -i0 -o0 -e0 \
   $PYTHON_CMD ./test_all.py \
   -v \
   --failfast \
   --plugins \
   --session vim \
   --vim $VIM \
   --expected-python-version $PYTHON_VERSION \
   2>&1 | ts '[%Y-%m-%d %H:%M:%S]'
