UltiSnips
=========

The official home of UltiSnips is at <https://github.com/sirver/ultisnips>.
Please add pull requests and issues there.

UltiSnips is the ultimate solution for snippets in Vim. It has tons of features
and is very fast.

Quick Start
-----------

This assumes you are using [Vundle](https://github.com/gmarik/Vundle.vim). Adapt
for your plugin manager of choice. Put this into your `.vimrc`.

    " Track the engine.
    Bundle 'SirVer/ultisnips'

    " Snippets are separated from the engine. Add this if you want them:
    Bundle 'honza/vim-snippets'

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

