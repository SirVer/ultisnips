MAKEFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
MAKEFILE_DIR := $(dir ${MAKEFILE_PATH})

# Test images as run on CI.
image_vim_74_py35:
	docker build -t ultisnips:$@ --build-arg PYTHON_IMAGE=3.5-stretch --build-arg VIM_VERSION=7.4 .
image_vim_80_py35:
	docker build -t ultisnips:$@ --build-arg PYTHON_IMAGE=3.5-stretch --build-arg VIM_VERSION=8.0 .
image_vim_81_py35:
	docker build -t ultisnips:$@ --build-arg PYTHON_IMAGE=3.5-stretch --build-arg VIM_VERSION=8.1 .
image_vim_82_py35:
	docker build -t ultisnips:$@ --build-arg PYTHON_IMAGE=3.5-stretch --build-arg VIM_VERSION=8.2 .
image_vim_git_py35:
	docker build -t ultisnips:$@ --build-arg PYTHON_IMAGE=3.5-stretch --build-arg VIM_VERSION=git .
image_vim_74_py36:
	docker build -t ultisnips:$@ --build-arg PYTHON_IMAGE=3.6-stretch --build-arg VIM_VERSION=7.4 .
image_vim_80_py36:
	docker build -t ultisnips:$@ --build-arg PYTHON_IMAGE=3.6-stretch --build-arg VIM_VERSION=8.0 .
image_vim_81_py36:
	docker build -t ultisnips:$@ --build-arg PYTHON_IMAGE=3.6-stretch --build-arg VIM_VERSION=8.1 .
image_vim_82_py36:
	docker build -t ultisnips:$@ --build-arg PYTHON_IMAGE=3.6-stretch --build-arg VIM_VERSION=8.2 .
image_vim_git_py36:
	docker build -t ultisnips:$@ --build-arg PYTHON_IMAGE=3.6-stretch --build-arg VIM_VERSION=git .
# 74 and 80 do not build with py37 and py38. The build errors out with "Require native threads".
image_vim_81_py37:
	docker build -t ultisnips:$@ --build-arg PYTHON_IMAGE=3.7-stretch --build-arg VIM_VERSION=8.1 .
image_vim_82_py37:
	docker build -t ultisnips:$@ --build-arg PYTHON_IMAGE=3.7-stretch --build-arg VIM_VERSION=8.2 .
image_vim_git_py37:
	docker build -t ultisnips:$@ --build-arg PYTHON_IMAGE=3.7-stretch --build-arg VIM_VERSION=git .
image_vim_81_py38:
	docker build -t ultisnips:$@ --build-arg PYTHON_IMAGE=3.8-buster --build-arg VIM_VERSION=8.1 .
image_vim_82_py38:
	docker build -t ultisnips:$@ --build-arg PYTHON_IMAGE=3.8-buster --build-arg VIM_VERSION=8.2 .
image_vim_git_py38:
	docker build -t ultisnips:$@ --build-arg PYTHON_IMAGE=3.8-buster --build-arg VIM_VERSION=git .
image_vim_81_py39:
	docker build -t ultisnips:$@ --build-arg PYTHON_IMAGE=3.9-buster --build-arg VIM_VERSION=8.1 .
image_vim_82_py39:
	docker build -t ultisnips:$@ --build-arg PYTHON_IMAGE=3.9-buster --build-arg VIM_VERSION=8.2 .
image_vim_git_py39:
	docker build -t ultisnips:$@ --build-arg PYTHON_IMAGE=3.9-buster --build-arg VIM_VERSION=git .

image_repro: image_vim_82_py39
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
