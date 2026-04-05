MAKEFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
MAKEFILE_DIR := $(dir ${MAKEFILE_PATH})

image_repro:
	docker build -t ultisnips:repro --build-arg PYTHON_IMAGE=3.13-bookworm --build-arg VIM_VERSION=git .

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

test_unit:
	PYTHONPATH=pythonx uv run pytest pythonx/UltiSnips/test_*.py

format:
	uv run ruff format .

lint:
	uv run ruff check .
