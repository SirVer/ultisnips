#!/bin/bash

set -o errexit
set -o verbose

mkdir -p /src && cd /src

if [[ $VIM_VERSION == "git" ]]; then
   git clone https://github.com/vim/vim
else
   curl -L https://github.com/vim/vim/archive/refs/tags/v${VIM_VERSION}.tar.gz  -o vim.tar.gz
   tar xf vim.tar.gz && rm vim.tar.gz
   mv -v vim* vim
fi
