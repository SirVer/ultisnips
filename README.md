![Build Status](https://github.com/SirVer/ultisnips/actions/workflows/main.yml/badge.svg)
[![Gitter](https://badges.gitter.im/Join%20Chat.svg)][chat] [![Documentation](https://img.shields.io/badge/documentation-open-blue)][documentation]

[chat]: https://gitter.im/SirVer/ultisnips?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge
[documentation]: https://github.com/SirVer/ultisnips/blob/master/doc/UltiSnips.txt

# UltiSnips

UltiSnips is the snippet engine for Vim.

> :warning: You have to install snippets separately via [this][snippets] plugin for instance.

[snippets]: https://github.com/honza/vim-snippets

## Features

There are example uses for some power user features here:

* [Snippets Aliases](doc/examples/snippets-aliasing/README.md)
* [Dynamic Tabstops/Tabstop Generation](doc/examples/tabstop-generation/README.md)

## Integrations

- [YouCompleteMe](https://github.com/Valloric/YouCompleteMe)
- [deoplete](https://github.com/Shougo/deoplete.nvim)
- [vim-easycomplete](https://github.com/jayli/vim-easycomplete)
- etc.

## Example

![GIF Demo](https://raw.github.com/SirVer/ultisnips/master/doc/demo.gif)

In this demo I am editing a python file. At first I expand the `#!` snippet, then
the `class` snippet. The completion menu comes from
[YouCompleteMe](https://github.com/Valloric/YouCompleteMe). I can
jump through placeholders and add text while the snippet inserts text in other
places automatically: when I add `Animal` as a base class, `__init__` gets
updated to call the base class constructor. When I add arguments to the
constructor, they automatically get assigned to instance variables. I then
insert my personal snippet for `print` debugging. Note that I left insert mode,
inserted another snippet and went back to add an additional argument to
`__init__` and the class snippet was still active and added another instance
variable.

## Installation

> You can use any way to install this plugin. It is not required to use plugin manager.

### [Vundle][Vundle.vim]

[Vundle.vim]: https://github.com/gmarik/Vundle.vim

```vim
" Track the engine.
Plugin 'SirVer/ultisnips'

" Snippets are separated from the engine.
Plugin 'honza/vim-snippets'

" If you want :UltiSnipsEdit to split your window.
let g:UltiSnipsEditSplit="vertical"
```

## Default configuration

```vim
let g:UltiSnipsExpandTrigger="<tab>"
let g:UltiSnipsJumpForwardTrigger="<c-b>"
let g:UltiSnipsJumpBackwardTrigger="<c-z>"
```

# Tutorials

From a gentle introduction to really advanced in a few minutes: the blog posts
of the screencasts contain more advanced examples of the things discussed in the
videos.

- [Episode 1: What are snippets and do I need them?](http://www.sirver.net/blog/2011/12/30/first-episode-of-ultisnips-screencast/)
- [Episode 2: Creating Basic Snippets](http://www.sirver.net/blog/2012/01/08/second-episode-of-ultisnips-screencast/)
- [Episode 3: What's new in version 2.0](http://www.sirver.net/blog/2012/02/05/third-episode-of-ultisnips-screencast/)
- [Episode 4: Python Interpolation](http://www.sirver.net/blog/2012/03/31/fourth-episode-of-ultisnips-screencast/)

Also the excellent [Vimcasts](http://vimcasts.org) dedicated three episodes to
UltiSnips:

- [Meet UltiSnips](http://vimcasts.org/episodes/meet-ultisnips/)
- [Using Python interpolation in UltiSnips snippets](http://vimcasts.org/episodes/ultisnips-python-interpolation/)
- [Using selected text in UltiSnips snippets](http://vimcasts.org/episodes/ultisnips-visual-placeholder/)


## History notes

UltiSnips was started in Jun 2009 by @SirVer. In Dec 2015, maintenance was
handed over to [@seletskiy](https://github.com/seletskiy) who ran out of time
in early 2017. Since Jun 2019, @SirVer is maintaining UltiSnips again on a
very constraint time budget. If you can help triaging issues it would be
greatly appreciated.
