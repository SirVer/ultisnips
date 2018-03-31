#!/bin/bash

set -o errexit
set -o verbose
set -o pipefail

# Cache intermediate Docker layers. For a description of how this works, see:
# https://giorgos.sealabs.net/docker-cache-on-travis-and-docker-112.html
if [[ ${TRAVIS_BRANCH} == "master" ]] && [[ ${TRAVIS_PULL_REQUEST} == "false" ]]; then
  mkdir -p $(dirname ${DOCKER_CACHE_FILE})
  IMAGE_NAMES=$(docker history -q ultisnips:${TAG} | grep -v '<missing>')
  docker save ${IMAGE_NAMES} | gzip > ${DOCKER_CACHE_FILE}.new
  mv ${DOCKER_CACHE_FILE}.new ${DOCKER_CACHE_FILE}
fi
