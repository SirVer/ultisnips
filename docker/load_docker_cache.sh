#!/bin/bash

set -o errexit
set -o verbose
set -o pipefail

# See
# https://giorgos.sealabs.net/docker-cache-on-travis-and-docker-112.html
if [ -f ${DOCKER_CACHE_FILE} ]; then
  gunzip -c ${DOCKER_CACHE_FILE} | docker load;
fi
