#!/bin/bash

set -o errexit
set -o verbose

mkdir -p /src && cd /src

if [[ $VIM_VERSION == "git" ]]; then
   git clone https://github.com/vim/vim
else
   curl https://github.com/vim/vim/archive/refs/tags/v${VIM_VERSION}.0.tar.gz  -o vim.tar.gz
   tar xf vim.tar.bz2
   mv -v vim?? vim
fi
