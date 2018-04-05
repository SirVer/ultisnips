ARG BASE_IMAGE

FROM ultisnips:${BASE_IMAGE}

RUN curl -fLo ~/.vim/autoload/plug.vim --create-dirs \
    https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim

ADD docker/docker_vimrc.vim /root/.vimrc
RUN vim -c 'PlugInstall | qa'

ADD docker/snippets /root/.vim/UltiSnips
