[![Build Status](https://travis-ci.org/SirVer/ultisnips.svg?branch=master)](https://travis-ci.org/SirVer/ultisnips)
[![Stories in Ready](https://badge.waffle.io/SirVer/ultisnips.png?label=ready&title=Ready)](https://waffle.io/SirVer/ultisnips)
[![Gitter](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/SirVer/ultisnips?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge)

UltiSnips
=========

UltiSnips is the ultimate solution for snippets in Vim. It has tons of features
and is very fast.

![GIF Demo](https://raw.github.com/SirVer/ultisnips/master/doc/demo.gif)

In this demo I am editing a python file. I first expand the `#!` snippet, then
the `class` snippet. The completion menu comes from
[YouCompleteMe](https://github.com/Valloric/YouCompleteMe), UltiSnips also
integrates with [neocomplete](https://github.com/Shougo/neocomplete.vim). I can
jump through placeholders and add text while the snippet inserts text in other
places automatically: when I add `Animal` as a base class, `__init__` gets
updated to call the base class constructor. When I add arguments to the
constructor, they automatically get assigned to instance variables. I then
insert my personal snippet for `print` debugging. Note that I left insert mode,
inserted another snippet and went back to add an additional argument to
`__init__` and the class snippet was still active and added another instance
variable.

The official home of UltiSnips is at <https://github.com/sirver/ultisnips>.
Please add pull requests and issues there.

Quick Start
-----------

This assumes you are using [Vundle](https://github.com/gmarik/Vundle.vim). Adapt
for your plugin manager of choice. Put this into your `.vimrc`.

    " Track the engine.
    Plugin 'SirVer/ultisnips'

    " Snippets are separated from the engine. Add this if you want them:
    Plugin 'honza/vim-snippets'

    " Trigger configuration. Do not use <tab> if you use https://github.com/Valloric/YouCompleteMe.
    let g:UltiSnipsExpandTrigger="<tab>"
    let g:UltiSnipsJumpForwardTrigger="<c-b>"
    let g:UltiSnipsJumpBackwardTrigger="<c-z>"

    " If you want :UltiSnipsEdit to split your window.
    let g:UltiSnipsEditSplit="vertical"

UltiSnips comes with comprehensive
[documentation](https://github.com/SirVer/ultisnips/blob/master/doc/UltiSnips.txt).
As there are more options and tons of features I suggest you at least skim it.

Screencasts
-----------

From a gentle introduction to really advanced in a few minutes. The blog posts
of the screencasts contain more advanced examples of the things
discussed in the videos.

- [Episode 1: What are snippets and do I need them?](http://www.sirver.net/blog/2011/12/30/first-episode-of-ultisnips-screencast/)
- [Episode 2: Creating Basic Snippets](http://www.sirver.net/blog/2012/01/08/second-episode-of-ultisnips-screencast/)
- [Episode 3: What's new in version 2.0](http://www.sirver.net/blog/2012/02/05/third-episode-of-ultisnips-screencast/)
- [Episode 4: Python Interpolation](http://www.sirver.net/blog/2012/03/31/fourth-episode-of-ultisnips-screencast/)

Also the excellent [Vimcasts](http://vimcasts.org) dedicated three episodes to
UltiSnips:

- [Meet UltiSnips](http://vimcasts.org/episodes/meet-ultisnips/)
- [Using Python interpolation in UltiSnips snippets](http://vimcasts.org/episodes/ultisnips-python-interpolation/)
- [Using selected text in UltiSnips snippets](http://vimcasts.org/episodes/ultisnips-visual-placeholder/)
