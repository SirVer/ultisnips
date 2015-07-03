#!/usr/bin/env bash

set -ex

VIM="${HOME}/bin/vim"
PYTHON="python${TRAVIS_PYTHON_VERSION}"
PYTHON_CMD="$(which ${PYTHON})"

# This is needed so that vim finds the shared libraries it was build against -
# they are not on the regular path.
export LD_LIBRARY_PATH="$($PYTHON-config --prefix)/lib"

if [[ $TRAVIS_PYTHON_VERSION =~ ^2\. ]]; then
   PY_IN_VIM="py"
else
   PY_IN_VIM="py3"
fi

echo "Using python from: $PYTHON_CMD Version: $($PYTHON_CMD --version 2>&1)"
echo "Using vim from: $VIM. Version: $($VIMn)"

printf "${PY_IN_VIM} import sys;print(sys.version);\nquit" | $VIM -e -V9myVimLog
cat myVimLog

tmux new -d -s vim

$PYTHON_CMD ./test_all.py -v --plugins --session vim --vim $VIM
