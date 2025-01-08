#!/bin/bash

set -o errexit
set -o verbose

mkdir -p /src && cd /src

if [[ $VIM_VERSION == "git" ]]; then
   git clone https://github.com/vim/vim
else
   curl https://ftp.nluug.nl/pub/vim/unix/vim-${VIM_VERSION}.tar.bz2 -o vim.tar.bz2
   tar xjf vim.tar.bz2
   mv -v vim?? vim
fi
