MAKEFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
MAKEFILE_DIR := $(dir ${MAKEFILE_PATH})

# Test images as run on CI.
image_vim_74_py2:
	docker build -t ultisnips:$@ --build-arg PYTHON_IMAGE=2.7-stretch --build-arg VIM_VERSION=7.4 .
image_vim_80_py2:
	docker build -t ultisnips:$@ --build-arg PYTHON_IMAGE=2.7-stretch --build-arg VIM_VERSION=8.0 .
image_vim_git_py2:
	docker build -t ultisnips:$@ --build-arg PYTHON_IMAGE=2.7-stretch --build-arg VIM_VERSION=git .
image_vim_74_py3:
	docker build -t ultisnips:$@ --build-arg PYTHON_IMAGE=3.6-stretch --build-arg VIM_VERSION=7.4 .
image_vim_80_py3:
	docker build -t ultisnips:$@ --build-arg PYTHON_IMAGE=3.6-stretch --build-arg VIM_VERSION=8.0 .
image_vim_git_py3:
	docker build -t ultisnips:$@ --build-arg PYTHON_IMAGE=3.6-stretch --build-arg VIM_VERSION=git .

image_repro: image_vim_80_py3
	docker build -t ultisnips:repro --build-arg BASE_IMAGE=$< -f Dockerfile.repro .

# A reproduction image that drops you into a naked environment,
# with a Vim having UltiSnips and vim-snippets configured. See
# docker/docker_vimrc.vim for the full vimrc. Need to run `make
# image_repro` before this will work.
repro:
	docker run -it -v ${MAKEFILE_DIR}:/src/UltiSnips ultisnips:repro /bin/bash

# This assumes, the repro image is already running and it opens an extra shell
# inside the running container
shell_in_repro:
	docker exec -it $(shell docker ps -q) /bin/bash
