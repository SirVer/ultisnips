#!/bin/bash

set -o errexit
set -o verbose

cd /src/vim

if [[ $PYTHON_VERSION =~ ^2\. ]]; then
   PYTHON_BUILD_CONFIG="--enable-pythoninterp"
else
   PYTHON_BUILD_CONFIG="--enable-python3interp"
fi

export CFLAGS="$(python-config --cflags)"
echo $CFLAGS
./configure \
   --disable-nls \
   --disable-sysmouse \
   --disable-gpm \
   --enable-gui=no \
   --enable-multibyte \
   --with-features=huge \
   --with-tlib=ncurses \
   --without-x \
   $PYTHON_BUILD_CONFIG || cat $(find . -name 'config.log')
make install
