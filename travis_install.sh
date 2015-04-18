#!/usr/bin/env bash

# Installs dependencies on travis and prepares the test run.
set -ex

env

# Install tmux (> 1.8) and vim. 
add-apt-repository ppa:kalakris/tmux -y
apt-get update -qq
apt-get install -qq -y tmux vim-gnome

# Clone the dependent plugins we want to use.
./test_all.py --clone-plugins

# Start the testing session.
tmux new -d -s vim
vim --version
