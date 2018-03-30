ARG PYTHON_IMAGE

FROM python:${PYTHON_IMAGE}

ARG VIM_VERSION

COPY scripts/install_packages.sh src/scripts/
RUN src/scripts/install_packages.sh
COPY scripts/download_vim.sh src/scripts/
RUN src/scripts/download_vim.sh
COPY scripts/build_vim.sh src/scripts/
RUN src/scripts/build_vim.sh

# We clone the plugins we currently depend on manually here. Initially we check if their master
# has changed since last time we build, this will invalidate the cache.
RUN mkdir -p /tmp/UltiSnips_test_vim_plugins

ADD https://api.github.com/repos/tpope/vim-pathogen/git/refs/heads/master \
    /src/scripts/vim-pathogen_version.json
RUN git clone --recursive --depth 1 https://github.com/tpope/vim-pathogen /tmp/UltiSnips_test_vim_plugins/vim-pathogen

ADD https://api.github.com/repos/ervandew/supertab/git/refs/heads/master \
    /src/scripts/supertab_version.json
RUN git clone --recursive --depth 1 https://github.com/ervandew/supertab /tmp/UltiSnips_test_vim_plugins/supertab

COPY . /src/UltiSnips
WORKDIR /src/UltiSnips
