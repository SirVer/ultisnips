#!/bin/bash

set -o errexit
set -o verbose

cd /src/vim

PYTHON_BUILD_CONFIG="--enable-python3interp"

export CFLAGS="$(python-config --cflags)"
echo $CFLAGS
./configure \
   --disable-gpm \
   --disable-nls \
   --disable-sysmouse \
   --enable-gui=no \
   --enable-multibyte \
   --enable-python3interp \
   --with-features=huge \
   --with-tlib=ncurses \
   --without-x \
   || cat $(find . -name 'config.log')
make install
