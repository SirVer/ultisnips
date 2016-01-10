# encoding: utf-8
from test.vim_test_case import VimTestCase as _VimTest
from test.constant import *
from test.util import running_on_windows

# AddSnippet Function  {{{#


class _AddFuncBase(_VimTest):
    args = ''

    def _before_test(self):
        self.vim.send_to_vim(':call UltiSnips#AddSnippetWithPriority(%s)\n' % self.args)


class AddFunc_Simple(_AddFuncBase):
    args = '"test", "simple expand", "desc", "", "all", 0'
    keys = 'abc test' + EX
    wanted = 'abc simple expand'


class AddFunc_Opt(_AddFuncBase):
    args = '".*test", "simple expand", "desc", "r", "all", 0'
    keys = 'abc test' + EX
    wanted = 'simple expand'
# End: AddSnippet Function  #}}}

# Langmap Handling  {{{#
# Test for bug 501727 #


class TestNonEmptyLangmap_ExpectCorrectResult(_VimTest):
    snippets = ('testme',
                """my snipped ${1:some_default}
and a mirror: $1
$2...$3
$0""")
    keys = 'testme' + EX + 'hi1' + JF + 'hi2' + JF + 'hi3' + JF + 'hi4'
    wanted = """my snipped hi1
and a mirror: hi1
hi2...hi3
hi4"""

    def _extra_vim_config(self, vim_config):
        vim_config.append('set langmap=dj,rk,nl,ln,jd,kr,DJ,RK,NL,LN,JD,KR')

# Test for https://bugs.launchpad.net/bugs/501727 #


class TestNonEmptyLangmapWithSemi_ExpectCorrectResult(_VimTest):
    snippets = ('testme',
                """my snipped ${1:some_default}
and a mirror: $1
$2...$3
$0""")
    keys = 'testme' + EX + 'hi;' + JF + 'hi2' + \
        JF + 'hi3' + JF + 'hi4' + ESC + ';Hello'
    wanted = """my snipped hi;
and a mirror: hi;
hi2...hi3
hi4Hello"""

    def _before_test(self):
        self.vim.send_to_vim(':set langmap=\\\\;;A\n')

# Test for bug 871357 #


class TestLangmapWithUtf8_ExpectCorrectResult(_VimTest):
    # SendKeys can't send UTF characters
    skip_if = lambda self: running_on_windows()
    snippets = ('testme',
                """my snipped ${1:some_default}
and a mirror: $1
$2...$3
$0""")
    keys = 'testme' + EX + 'hi1' + JF + 'hi2' + JF + 'hi3' + JF + 'hi4'
    wanted = """my snipped hi1
and a mirror: hi1
hi2...hi3
hi4"""

    def _before_test(self):
        self.vim.send_to_vim(
            ":set langmap=йq,цw,уe,кr,еt,нy,гu,шi,щo,зp,х[,ъ],фa,ыs,вd,аf,пg,рh,оj,лk,дl,ж\\;,э',яz,чx,сc,мv,иb,тn,ьm,ю.,ё',ЙQ,ЦW,УE,КR,ЕT,НY,ГU,ШI,ЩO,ЗP,Х\{,Ъ\},ФA,ЫS,ВD,АF,ПG,РH,ОJ,ЛK,ДL,Ж\:,Э\",ЯZ,ЧX,СC,МV,ИB,ТN,ЬM,Б\<,Ю\>\n")

# End: Langmap Handling  #}}}

# SnippetsInCurrentScope  {{{#


class VerifyVimDict1(_VimTest):

    """check:
    correct type (4 means vim dictionary)
    correct length of dictionary (in this case we have on element if the use same prefix, dictionary should have 1 element)
    correct description (including the apostrophe)
    if the prefix is mismatched no resulting dict should have 0 elements
    """

    snippets = ('testâ', 'abc123ά', '123\'êabc')
    keys = ('test=(type(UltiSnips#SnippetsInCurrentScope()) . len(UltiSnips#SnippetsInCurrentScope()) . ' +
            'UltiSnips#SnippetsInCurrentScope()["testâ"]' + ')\n' +
            '=len(UltiSnips#SnippetsInCurrentScope())\n')

    wanted = 'test41123\'êabc0'


class VerifyVimDict2(_VimTest):

    """check:
    can use " in trigger
    """

    snippets = ('te"stâ', 'abc123ά', '123êabc')
    akey = "'te{}stâ'".format('"')
    keys = (
        'te"=(UltiSnips#SnippetsInCurrentScope()[{}]'.format(akey) + ')\n')
    wanted = 'te"123êabc'


class VerifyVimDict3(_VimTest):

    """check:
    can use ' in trigger
    """

    snippets = ("te'stâ", 'abc123ά', '123êabc')
    akey = '"te{}stâ"'.format("'")
    keys = (
        "te'=(UltiSnips#SnippetsInCurrentScope()[{}]".format(akey) + ')\n')
    wanted = "te'123êabc"
# End: SnippetsInCurrentScope  #}}}

# Snippet Source  {{{#


class AddNewSnippetSource(_VimTest):
    keys = ('blumba' + EX + ESC +
            ':%(python)s UltiSnips_Manager.register_snippet_source(' +
            "'temp', MySnippetSource())\n" +
            'oblumba' + EX + ESC +
            ":%(python)s UltiSnips_Manager.unregister_snippet_source('temp')\n" +
            'oblumba' + EX) % {'python': 'py3' if PYTHON3 else 'py'}
    wanted = (
        'blumba' + EX + '\n' +
        'this is a dynamic snippet' + '\n' +
        'blumba' + EX
    )

    def _extra_vim_config(self, vim_config):
        self._create_file('snippet_source.py', """
from UltiSnips.snippet.source import SnippetSource
from UltiSnips.snippet.definition import UltiSnipsSnippetDefinition

class MySnippetSource(SnippetSource):
  def get_snippets(self, filetypes, before, possible, autotrigger_only):
    if before.endswith('blumba') and autotrigger_only == False:
      return [
          UltiSnipsSnippetDefinition(
              -100, "blumba", "this is a dynamic snippet", "", "", {}, "blub",
              None, {})
        ]
    return []
""")
        pyfile = 'py3file' if PYTHON3 else 'pyfile'
        vim_config.append(
            '%s %s' %
            (pyfile, self.name_temp('snippet_source.py')))
# End: Snippet Source  #}}}
