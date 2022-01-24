#!/usr/bin/env bash

set -e

PYTHON_CMD="$(which python)"
VIM="/usr/local/bin/vim"
PYTHON_VERSION=$($PYTHON_CMD -c 'import sys;print(sys.version.split()[0])')
echo "Using python from: $PYTHON_CMD Version: $PYTHON_VERSION"
echo "Using vim from: $VIM"
$VIM --version | head -n 3

set -x

tmux new -d -s vim

# Tests on CI sometimes hang, but we do not know which test it is for sure,
# since all we see are lines of the prior passed tests. In an attempt to have
# every character appear unbuffered we hope to uncover where the test actually
# hangs.
# We also use the `ts` tool to inform us when each line was printed to increase
# the likelyhood to find the failing test faster. Adding these debug helps seem
# to have reduced the likelyhood of the tests failing though.
# See https://stackoverflow.com/questions/3465619/how-to-make-output-of-any-shell-command-unbuffered/25548995
stdbuf -i0 -o0 -e0 \
   $PYTHON_CMD ./test_all.py \
   -v \
   --failfast \
   --plugins \
   --session vim \
   --vim $VIM \
   --interface tmux \
   --expected-python-version $PYTHON_VERSION \
   2>&1 | ts '[%Y-%m-%d %H:%M:%S]'
