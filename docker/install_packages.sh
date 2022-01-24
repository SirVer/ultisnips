#!/bin/sh

set -o errexit
set -o verbose

apt-get update
apt-get install -y \
    g++ \
    moreutils \
    tmux \
    git
apt-get clean
