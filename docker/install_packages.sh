#!/bin/sh

set -o errexit
set -o verbose

apt-get update
apt-get install -y \
    g++ \
    tmux \
    git
apt-get clean
