#!/usr/bin/env bash

set -ex

PYTHON="python${TRAVIS_PYTHON_VERSION}"
PYTHON_CMD="$(which ${PYTHON})"

if [[ $VIM_VERSION = "74" || $VIM_VERSION = "mercurial" ]]; then
   INTERFACE="--interface tmux"
   VIM="${HOME}/bin/vim"
   # This is needed so that vim finds the shared libraries it was build against -
   # they are not on the regular path.
   export LD_LIBRARY_PATH="$($PYTHON-config --prefix)/lib"

elif [[ $VIM_VERSION == "NEOVIM" ]]; then
   VIM="$(which nvim)"
   if [[ $TRAVIS_PYTHON_VERSION =~ ^2\. ]]; then
      INTERFACE="--interface tmux_nvim --python-host-prog=$PYTHON_CMD"
      PY_IN_VIM="py"
   else
      INTERFACE="--interface tmux_nvim --python3-host-prog=$PYTHON_CMD"
      PY_IN_VIM="py3"
   fi
else
   echo "Unknown VIM_VERSION: $VIM_VERSION"
   exit 1
fi

if [[ $TRAVIS_PYTHON_VERSION =~ ^2\. ]]; then
   PY_IN_VIM="py"
else
   PY_IN_VIM="py3"
fi

echo "Using python from: $PYTHON_CMD Version: $($PYTHON_CMD --version 2>&1)"
echo "Using vim from: $VIM. Version: $($VIMn)"

tmux new -d -s vim

$PYTHON_CMD ./test_all.py -v --plugins $INTERFACE --session vim --vim $VIM
