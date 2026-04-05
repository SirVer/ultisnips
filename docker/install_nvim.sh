#!/bin/bash

set -o errexit
set -o verbose

cd /tmp

curl -LO "https://github.com/neovim/neovim/releases/download/v${NVIM_VERSION}/nvim-linux-x86_64.tar.gz"
tar xzf nvim-linux-x86_64.tar.gz
cp -r nvim-linux-x86_64/* /usr/local/
rm -rf nvim-linux-x86_64 nvim-linux-x86_64.tar.gz

nvim --version
