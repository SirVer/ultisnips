from test.constant import ARR_L, ARR_U, ESC, EX, JF
from test.vim_test_case import VimTestCase as _VimTest


class SnippetActions_PreActionModifiesBuffer(_VimTest):
    files = {
        "us/all.snippets": r"""
        pre_expand "snip.buffer[snip.line:snip.line] = ['\n']"
        snippet a "desc" "True" e
        abc
        endsnippet
        """
    }
    keys = "a" + EX
    wanted = "\nabc"


class SnippetActions_PostActionModifiesBuffer(_VimTest):
    files = {
        "us/all.snippets": r"""
        post_expand "snip.buffer[snip.line+1:snip.line+1] = ['\n']"
        snippet a "desc" "True" e
        abc
        endsnippet
        """
    }
    keys = "a" + EX
    wanted = "abc\n"


class SnippetActions_ErrorOnBufferModificationThroughCommand(_VimTest):
    files = {
        "us/all.snippets": r"""
        pre_expand "vim.command('normal O')"
        snippet a "desc" "True" e
        abc
        endsnippet
        """
    }
    keys = "a" + EX
    expected_error = "changes are untrackable"


class SnippetActions_ErrorOnModificationSnippetLine(_VimTest):
    files = {
        "us/all.snippets": r"""
        post_expand "vim.command('normal dd')"
        snippet i "desc" "True" e
        if:
            $1
        endsnippet
        """
    }
    keys = "i" + EX
    expected_error = "line under the cursor was modified"


class SnippetActions_EnsureIndent(_VimTest):
    files = {
        "us/all.snippets": r"""
        pre_expand "snip.buffer[snip.line] = ' '*4; snip.cursor[1] = 4"
        snippet i "desc" "True" e
        if:
            $1
        endsnippet
        """
    }
    keys = "\ni" + EX + "i" + EX + "x"
    wanted = """
    if:
    if:
        x"""


class SnippetActions_PostActionCanUseSnippetRange(_VimTest):
    files = {
        "us/all.snippets": r"""
        global !p
        def ensure_newlines(start, end):
            snip.buffer[start[0]:start[0]] = ['\n'] * 2
            snip.buffer[end[0]+1:end[0]+1] = ['\n'] * 1
        endglobal

        post_expand "ensure_newlines(snip.snippet_start, snip.snippet_end)"
        snippet i "desc"
        if
            $1
        else
            $2
        end
        endsnippet
        """
    }
    keys = "\ni" + EX + "x" + JF + "y"
    wanted = """


if
    x
else
    y
end
"""


class SnippetActions_CanModifyParentBody(_VimTest):
    files = {
        "us/all.snippets": r"""
        global !p
        def ensure_newlines(start, end):
            snip.buffer[start[0]:start[0]] = ['\n'] * 2
        endglobal

        post_expand "ensure_newlines(snip.snippet_start, snip.snippet_end)"
        snippet i "desc"
        if
            $1
        else
            $2
        end
        endsnippet
        """
    }
    keys = "\ni" + EX + "i" + EX + "x" + JF + "y" + JF + JF + "z"
    wanted = """


if


    if
        x
    else
        y
    end
else
    z
end"""


class SnippetActions_MoveParentSnippetFromChildInPreAction(_VimTest):
    files = {
        "us/all.snippets": r"""
        global !p
        def insert_import():
            snip.buffer[2:2] = ['import smthing', '']
        endglobal

        pre_expand "insert_import()"
        snippet p "desc"
        print(smthing.traceback())
        endsnippet

        snippet i "desc"
        if
            $1
        else
            $2
        end
        endsnippet
        """
    }
    keys = "i" + EX + "p" + EX + JF + "z"
    wanted = """import smthing

if
    print(smthing.traceback())
else
    z
end"""


class SnippetActions_CanExpandSnippetInDifferentPlace(_VimTest):
    files = {
        "us/all.snippets": r"""
        global !p
        def expand_after_if(snip):
            snip.buffer[snip.line] = snip.buffer[snip.line][:snip.column] + \
                snip.buffer[snip.line][snip.column+1:]
            snip.cursor[1] = snip.buffer[snip.line].index('if ')+3
        endglobal

        pre_expand "expand_after_if(snip)"
        snippet n "append not to if" w
        not $0
        endsnippet

        snippet i "if cond" w
        if $1: $2
        endsnippet
        """
    }
    keys = "i" + EX + "blah" + JF + "n" + EX + JF + "pass"
    wanted = """if not blah: pass"""


class SnippetActions_MoveVisual(_VimTest):
    files = {
        "us/all.snippets": r"""
        global !p
        def extract_method(snip):
            del snip.buffer[snip.line]
            snip.buffer[len(snip.buffer)-1:len(snip.buffer)-1] = ['']
            snip.cursor.set(len(snip.buffer)-2, 0)
        endglobal

        pre_expand "extract_method(snip)"
        snippet n "append not to if" w
        def $1:
            ${VISUAL}

        endsnippet
        """
    }

    keys = (
        """
def a:
    x()
    y()
    z()"""
        + ESC
        + "kVk"
        + EX
        + "n"
        + EX
        + "b"
    )

    wanted = """
def a:
    z()

def b:
    x()
    y()"""


class SnippetActions_CanMirrorTabStopsOutsideOfSnippet(_VimTest):
    files = {
        "us/all.snippets": r"""
        post_jump "snip.buffer[2] = 'debug({})'.format(snip.tabstops[1].current_text)"
        snippet i "desc"
        if $1:
            $2
        endsnippet
        """
    }
    keys = (
        """
---
i"""
        + EX
        + "test(some(complex(cond(a))))"
        + JF
        + "x"
    )
    wanted = """debug(test(some(complex(cond(a)))))
---
if test(some(complex(cond(a)))):
    x"""


class SnippetActions_CanExpandAnonSnippetInJumpAction(_VimTest):
    files = {
        "us/all.snippets": r"""
        global !p
        def expand_anon(snip):
            if snip.tabstop == 0:
                snip.expand_anon("a($2, $1)")
        endglobal

        post_jump "expand_anon(snip)"
        snippet i "desc"
        if ${1:cond}:
            $0
        endsnippet
        """
    }
    keys = "i" + EX + "x" + JF + "1" + JF + "2" + JF + ";"
    wanted = """if x:
    a(2, 1);"""


class SnippetActions_CanExpandAnonSnippetInJumpActionWhileSelected(_VimTest):
    files = {
        "us/all.snippets": r"""
        global !p
        def expand_anon(snip):
            if snip.tabstop == 0:
                snip.expand_anon(" // a($2, $1)")
        endglobal

        post_jump "expand_anon(snip)"
        snippet i "desc"
        if ${1:cond}:
            ${2:pass}
        endsnippet
        """
    }
    keys = "i" + EX + "x" + JF + JF + "1" + JF + "2" + JF + ";"
    wanted = """if x:
    pass // a(2, 1);"""


class SnippetActions_CanUseContextFromContextMatch(_VimTest):
    files = {
        "us/all.snippets": r"""
        pre_expand "snip.buffer[snip.line:snip.line] = [snip.context]"
        snippet i "desc" "'some context'" e
        body
        endsnippet
        """
    }
    keys = "i" + EX
    wanted = """some context
body"""


class SnippetActions_CanExpandAnonSnippetOnFirstJump(_VimTest):
    files = {
        "us/all.snippets": r"""
        global !p
        def expand_new_snippet_on_first_jump(snip):
            if snip.tabstop == 1:
                snip.expand_anon("some_check($1, $2, $3)")
        endglobal

        post_jump "expand_new_snippet_on_first_jump(snip)"
        snippet "test" "test new features" "True" bwre
        if $1: $2
        endsnippet
        """
    }
    keys = "test" + EX + "1" + JF + "2" + JF + "3" + JF + " or 4" + JF + "5"
    wanted = """if some_check(1, 2, 3) or 4: 5"""


class SnippetActions_CanExpandAnonOnPreExpand(_VimTest):
    files = {
        "us/all.snippets": r"""
        pre_expand "snip.buffer[snip.line] = ''; snip.expand_anon('totally_different($2, $1)')"
        snippet test "test new features" wb
        endsnippet
        """
    }
    keys = "test" + EX + "1" + JF + "2" + JF + "3"
    wanted = """totally_different(2, 1)3"""


class SnippetActions_CanEvenWrapSnippetInPreAction(_VimTest):
    files = {
        "us/all.snippets": r"""
        pre_expand "snip.buffer[snip.line] = ''; snip.expand_anon('some_wrapper($1): $2')"
        snippet test "test new features" wb
        wrapme($2, $1)
        endsnippet
        """
    }
    keys = "test" + EX + "1" + JF + "2" + JF + "3" + JF + "4"
    wanted = """some_wrapper(wrapme(2, 1)3): 4"""


class SnippetActions_CanVisuallySelectFirstPlaceholderInAnonSnippetInPre(_VimTest):
    files = {
        "us/all.snippets": r"""
        pre_expand "snip.buffer[snip.line] = ''; snip.expand_anon('${1:asd}, ${2:blah}')"
        snippet test "test new features" wb
        endsnippet
        """
    }
    keys = "test" + EX + "1" + JF + "2"
    wanted = """1, 2"""


class SnippetActions_UseCorrectJumpActions(_VimTest):
    files = {
        "us/all.snippets": r"""
        post_jump "snip.buffer[-2:-2]=['a' + str(snip.tabstop)]"
        snippet a "a" wb
        $1 {
        $2
        }
        endsnippet

        snippet b "b" wb
        bbb
        endsnippet

        post_jump "snip.buffer[-2:-2]=['c' + str(snip.tabstop)]"
        snippet c "c" w
        $1 : $2 : $3
        endsnippet
        """
    }
    keys = (
        "a" + EX + "1" + JF + "b" + EX + " c" + EX + "2" + JF + "3" + JF + "4" + JF + JF
    )
    wanted = """1 {
bbb 2 : 3 : 4
}
a1
a2
c1
c2
c3
c0
a0"""


class SnippetActions_PostActionModifiesCharAfterSnippet(_VimTest):
    files = {
        "us/all.snippets": r"""
        post_expand "snip.buffer[snip.snippet_end[0]] = snip.buffer[snip.snippet_end[0]][:-1]"
        snippet a "desc" i
        ($1)
        endsnippet
        """
    }
    keys = "[]" + ARR_L + "a" + EX + "1" + JF + "2"
    wanted = "[(1)2"


class SnippetActions_PostActionModifiesLineAfterSnippet(_VimTest):
    files = {
        "us/all.snippets": r"""
        post_expand "snip.buffer[snip.snippet_end[0]+1:snip.snippet_end[0]+2] = []"
        snippet a "desc"
        1: $1
        $0
        endsnippet
        """
    }
    keys = "\n3" + ARR_U + "a" + EX + "1" + JF + "2"
    wanted = "1: 1\n2"


class SnippetActions_DoNotBreakCursorOnSingleLikeChange(_VimTest):
    files = {
        "us/all.snippets": r"""
        post_expand "snip.buffer[snip.snippet_end[0]] = 'def'; snip.cursor.preserve()"
        snippet a "desc"
        asd
        endsnippet
        """
    }
    keys = "a" + EX + "123"
    wanted = "def123"


# GH #1115: expand_anon called from post_jump must place the cursor at the
# first tabstop *after* any leading literal text, not one column to its left.
class SnippetActions_ExpandAnonLeadingTextBeforeTabstop(_VimTest):
    files = {
        "us/all.snippets": r"""
        global !p
        def add_bullet(snip):
            if snip.tabstop == 0:
                snip.buffer[snip.line] = ''
                snip.expand_anon('- $1')
        endglobal

        post_jump "add_bullet(snip)"
        snippet bullet "" b
        endsnippet
        """
    }
    keys = "bullet" + EX + "X"
    wanted = "- X"


class SnippetActions_ExpandAnonLeadingTextBeforeTabstop_Multi(_VimTest):
    files = {
        "us/all.snippets": r"""
        global !p
        def add_bullets(snip):
            if snip.tabstop == 0:
                snip.buffer[snip.line] = ''
                snip.expand_anon('- $1\n- $2\n- $3')
        endglobal

        post_jump "add_bullets(snip)"
        snippet bullets "" b
        endsnippet
        """
    }
    keys = "bullets" + EX + "X" + JF + "Y" + JF + "Z"
    wanted = "- X\n- Y\n- Z"


# Mirror of the user's repro in GH #1115: regex trigger captures a digit,
# the snippet body returns it via `!p snip.rv = match.group(1)` (so the
# captured digit goes onto the current line), and post_jump expands an
# anonymous snippet that builds N bullet points with leading `- ` text.
class SnippetActions_ExpandAnonLeadingTextBeforeTabstop_AsInGH1115(_VimTest):
    files = {
        "us/all.snippets": r"""
        global !p
        def create_dotpoints(snip):
            try:
                amount = int(snip.buffer[snip.line].strip())
            except:
                amount = 1
            snip.buffer[snip.line] = ''
            body = ''
            for i in range(amount):
                body += '- $' + str(i+1) + '\n'
            snip.expand_anon(body)
        endglobal

        post_jump "create_dotpoints(snip)"
        snippet "stnd\.(\d?)" "Adds dot-points" br
        `!p snip.rv = match.group(1)`
        endsnippet
        """
    }
    keys = "stnd.3" + EX + "A" + JF + "B" + JF + "C"
    wanted = "- A\n- B\n- C\n"


# GH #1281: `snip.expand_anon()` parses its argument as a snippet body, so
# backticks/`$`/`\` from the buffer get interpreted as shell code / tabstops
# / escape sequences -- the full DSL is intentionally available.  This pins
# down what happens when arbitrary text is passed through unescaped: a pair
# of backticks is read as an empty shell-code block and disappears.
class SnippetActions_ExpandAnonReparsesBackticks_GH1281(_VimTest):
    files = {
        "us/all.snippets": """
        global !p
        def echo_line(snip):
            if snip.tabstop == 0:
                snip.expand_anon('> ' + snip.buffer[snip.line])
        endglobal

        post_jump "echo_line(snip)"
        snippet bug "" w
        endsnippet
        """
    }
    keys = "test with ``quotes'' bug" + EX
    # The `` pair is read as an empty shell-code block and disappears.
    wanted = "test with ``quotes'' > test with quotes'' "


# GH #1281: When arbitrary buffer text is spliced into an `expand_anon`
# argument, the DSL characters must be escaped first so they survive as
# literal text; this test pins down the documented escape recipe.
class SnippetActions_ExpandAnonEscapeBufferText_GH1281(_VimTest):
    files = {
        "us/all.snippets": """
        global !p
        def echo_line(snip):
            if snip.tabstop == 0:
                text = snip.buffer[snip.line]
                safe = text.replace('\\\\', '\\\\\\\\')
                safe = safe.replace('`', '\\\\`').replace('$', '\\\\$')
                snip.expand_anon('> ' + safe)
        endglobal

        post_jump "echo_line(snip)"
        snippet bug "" w
        endsnippet
        """
    }
    keys = "test with ``quotes'' bug" + EX
    wanted = "test with ``quotes'' > test with ``quotes'' "
