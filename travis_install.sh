#!/usr/bin/env bash

# Installs dependencies on travis and prepares the test run.
set -ex

build_vim () {
   URL=$1; shift; 
   curl $URL -o /tmp/vim.tar.bz2
   tar xjvf /tmp/vim.tar.bz2 -C /tmp
   cd /tmp/vim${VIM_VERSION}

   ./configure \
      --prefix=${HOME} \
      --disable-nls \
      --enable-gui=no \
      --enable-multibyte \
      --enable-pythoninterp \
      --with-features=huge \
      --with-tlib=ncurses \
      --without-x
   make install
}

if [[ $VIM_VERSION = "73" ]]; then
   build_vim ftp://ftp.vim.org/pub/vim/unix/vim-7.3.tar.bz2
elif [[ $VIM_VERSION = "74" ]]; then
   build_vim ftp://ftp.vim.org/pub/vim/unix/vim-7.4.tar.bz2
fi

# Install tmux (> 1.8) and vim. 
add-apt-repository ppa:kalakris/tmux -y
apt-get update -qq
apt-get install -qq -y tmux vim-gnome

# Clone the dependent plugins we want to use.
./test_all.py --clone-plugins

# Start the testing session.
tmux new -d -s vim
vim --version
