#!/usr/bin/env bash

# Installs a known version of vim in the travis test runner.

set -ex

PYTHON="python${TRAVIS_PYTHON_VERSION}"

build_vanilla_vim () {
   mkdir ~/vim_build
   pushd ~/vim_build

   if [[ $VIM_VERSION == "74" ]]; then
      until curl ftp://ftp.vim.org/pub/vim/unix/vim-7.4.tar.bz2 -o vim.tar.bz2; do sleep 10; done
      tar xjf vim.tar.bz2
      cd vim${VIM_VERSION}
   elif [[ $VIM_VERSION == "git" ]]; then
      git clone https://github.com/vim/vim
      cd vim
   fi

   local PYTHON_CONFIG_DIR=$(dirname $(find $($PYTHON-config --prefix)/lib -iname 'config.c') | grep $TRAVIS_PYTHON_VERSION)
   local PYTHON_BUILD_CONFIG=""
   if [[ $TRAVIS_PYTHON_VERSION =~ ^2\. ]]; then
      PYTHON_BUILD_CONFIG="--enable-pythoninterp --with-python-config-dir=${PYTHON_CONFIG_DIR}"
   else
      PYTHON_BUILD_CONFIG="--enable-python3interp --with-python3-config-dir=${PYTHON_CONFIG_DIR}"
   fi
   export LDFLAGS="$($PYTHON-config --ldflags) -L$($PYTHON-config --prefix)/lib"
   export CFLAGS="$($PYTHON-config --cflags)"

   # This is needed so that vim finds the shared libraries it was build against
   # - they are not on the regular path.
   export LD_LIBRARY_PATH="$($PYTHON-config --prefix)/lib"

   echo $LDFLAGS
   echo $CFLAGS
   ./configure \
      --prefix=${HOME} \
      --disable-nls \
      --disable-sysmouse \
      --disable-gpm \
      --enable-gui=no \
      --enable-multibyte \
      --with-features=huge \
      --with-tlib=ncurses \
      --without-x \
      ${PYTHON_BUILD_CONFIG} || cat $(find . -name 'config.log')

   make install
   popd

   rm -rf vim_build
}

if [[ $VIM_VERSION = "74" || $VIM_VERSION = "git" ]]; then
   build_vanilla_vim
elif [[ $VIM_VERSION == "NEOVIM" ]]; then
   PIP=$(which pip)
   $PIP install neovim
else
   echo "Unknown VIM_VERSION: $VIM_VERSION"
   exit 1
fi

# Clone the dependent plugins we want to use.
PYTHON_CMD="$(which $PYTHON)"
$PYTHON_CMD ./test_all.py --clone-plugins
