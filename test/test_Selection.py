from test.vim_test_case import VimTestCase as _VimTest
from test.constant import *

# Unmap SelectMode Mappings  {{{#
# Test for bug 427298 #


class _SelectModeMappings(_VimTest):
    snippets = ('test', '${1:World}')
    keys = 'test' + EX + 'Hello'
    wanted = 'Hello'
    maps = ('', '')
    buffer_maps = ('', '')
    do_unmapping = True
    ignores = []

    def _extra_vim_config(self, vim_config):
        vim_config.append(
            ':let g:UltiSnipsRemoveSelectModeMappings=%i' % int(
                self.do_unmapping))
        vim_config.append(
            ':let g:UltiSnipsMappingsToIgnore=%s' %
            repr(
                self.ignores))

        if not isinstance(self.maps[0], tuple):
            self.maps = (self.maps,)
        if not isinstance(self.buffer_maps[0], tuple):
            self.buffer_maps = (self.buffer_maps,)

        for key, m in self.maps:
            if not len(key):
                continue
            vim_config.append(':smap %s %s' % (key, m))
        for key, m in self.buffer_maps:
            if not len(key):
                continue
            vim_config.append(':smap <buffer> %s %s' % (key, m))


class SelectModeMappings_RemoveBeforeSelecting_ECR(_SelectModeMappings):
    maps = ('H', 'x')
    wanted = 'Hello'


class SelectModeMappings_DisableRemoveBeforeSelecting_ECR(_SelectModeMappings):
    do_unmapping = False
    maps = ('H', 'x')
    wanted = 'xello'


class SelectModeMappings_IgnoreMappings_ECR(_SelectModeMappings):
    ignores = ['e']
    maps = ('H', 'x'), ('e', 'l')
    wanted = 'Hello'


class SelectModeMappings_IgnoreMappings1_ECR(_SelectModeMappings):
    ignores = ['H']
    maps = ('H', 'x'), ('e', 'l')
    wanted = 'xello'


class SelectModeMappings_IgnoreMappings2_ECR(_SelectModeMappings):
    ignores = ['e', 'H']
    maps = ('e', 'l'), ('H', 'x')
    wanted = 'xello'


class SelectModeMappings_BufferLocalMappings_ECR(_SelectModeMappings):
    buffer_maps = ('H', 'blah')
    wanted = 'Hello'
# End: Unmap SelectMode Mappings  #}}}

# Exclusive Selection  {{{#


class _ES_Base(_VimTest):

    def _extra_vim_config(self, vim_config):
        vim_config.append('set selection=exclusive')


class ExclusiveSelection_SimpleTabstop_Test(_ES_Base):
    snippets = ('test', 'h${1:blah}w $1')
    keys = 'test' + EX + 'ui' + JF
    wanted = 'huiw ui'


class ExclusiveSelection_RealWorldCase_Test(_ES_Base):
    snippets = ('for',
                """for ($${1:i} = ${2:0}; $$1 < ${3:count}; $$1${4:++}) {
	${5:// code}
}""")
    keys = 'for' + EX + 'k' + JF
    wanted = """for ($k = 0; $k < count; $k++) {
	// code
}"""
# End: Exclusive Selection  #}}}

# Old Selection {{{#


class _OS_Base(_VimTest):

    def _extra_vim_config(self, vim_config):
        vim_config.append('set selection=old')


class OldSelection_SimpleTabstop_Test(_OS_Base):
    snippets = ('test', 'h${1:blah}w $1')
    keys = 'test' + EX + 'ui' + JF
    wanted = 'huiw ui'


class OldSelection_RealWorldCase_Test(_OS_Base):
    snippets = ('for',
                """for ($${1:i} = ${2:0}; $$1 < ${3:count}; $$1${4:++}) {
	${5:// code}
}""")
    keys = 'for' + EX + 'k' + JF
    wanted = """for ($k = 0; $k < count; $k++) {
	// code
}"""
# End: Old Selection #}}}
