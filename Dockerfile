ARG PYTHON_IMAGE

FROM python:${PYTHON_IMAGE}

ARG VIM_VERSION

COPY docker/install_packages.sh src/scripts/
RUN src/scripts/install_packages.sh
COPY docker/download_vim.sh src/scripts/
RUN src/scripts/download_vim.sh
COPY docker/build_vim.sh src/scripts/
RUN src/scripts/build_vim.sh

RUN pip install unidecode

COPY . /src/UltiSnips
WORKDIR /src/UltiSnips

RUN ./test_all.py --clone-plugins
