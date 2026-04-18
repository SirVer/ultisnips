MAKEFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
MAKEFILE_DIR := $(dir ${MAKEFILE_PATH})

image_repro:
	docker build -t ultisnips:repro --build-arg PYTHON_IMAGE=3.13-bookworm --build-arg VIM_VERSION=git .

# Neovim variant.  Uses Dockerfile.nvim (same one CI uses for nvim jobs)
# with the version pinned to what CI tests.  Run `make image_repro_nvim`
# before `make repro_nvim`.
image_repro_nvim:
	docker build -t ultisnips:repro_nvim -f Dockerfile.nvim --build-arg PYTHON_IMAGE=3.13-bookworm --build-arg NVIM_VERSION=0.12.0 .

# A reproduction image that drops you into a naked environment,
# with a Vim having UltiSnips and vim-snippets configured. See
# docker/docker_vimrc.vim for the full vimrc. Need to run `make
# image_repro` before this will work.
repro:
	docker run -it -v ${MAKEFILE_DIR}:/src/UltiSnips ultisnips:repro /bin/bash

# Neovim reproduction shell.  Once inside, start `tmux new -s vim` then
# run `./test_all.py --vim nvim` (or a subset).
repro_nvim:
	docker run -it -v ${MAKEFILE_DIR}:/src/UltiSnips ultisnips:repro_nvim /bin/bash

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
