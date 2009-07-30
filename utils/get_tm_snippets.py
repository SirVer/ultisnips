#!/usr/bin/env python
# encoding: utf-8

import urllib
import re
from xml.etree import ElementTree
from xml.parsers.expat import ExpatError
import htmlentitydefs

_UNESCAPE = re.compile(ur'&\w+?;', re.UNICODE)
def unescape(s):
    if s is None:
        return ""
    def fixup(m):
        ent = m.group(0)[1:-1]
        print ent
        return unichr(htmlentitydefs.name2codepoint[ent])
    try:
        return _UNESCAPE.sub(fixup,s.decode("utf-8")).encode("utf-8")
    except:
        print repr(s)

def parse_content(c):
    try:
        data = ElementTree.fromstring(c)[0]

        rv = {}
        for k,v in zip(data[::2], data[1::2]):
            rv[k.text] = unescape(v.text)

        return rv
    except ExpatError:
        print "   Syntax Error"
        return None

def fetch_snippets(name):
    base_url = "http://svn.textmate.org/trunk/Bundles/" + name + ".tmbundle/"
    snippet_idx = base_url + "Snippets/"

    idx_list = urllib.urlopen(snippet_idx).read()


    rv = []
    for link in re.findall("<li>(.*?)</li>", idx_list):
        m = re.match(r'<a\s*href="(.*)"\s*>(.*)</a>', link)
        link, name = m.groups()
        if name == "..":
            continue

        name = unescape(name.rsplit('.', 1)[0]) # remove Extension
        print "Fetching data for Snippet '%s'" % name
        content = urllib.urlopen(snippet_idx + link).read()

        cont = parse_content(content)
        if cont:
            rv.append((name, cont))

    return rv


def write_snippets(snip_descr, f):

    for name, d in snip_descr:
        if "tabTrigger" not in d:
            continue

        f.write('snippet %s "%s"\n' % (d["tabTrigger"], name))
        f.write(d["content"].encode("utf-8") + "\n")
        f.write("endsnippet\n\n")



if __name__ == '__main__':
    import sys

    bundle = sys.argv[1]
    rv = fetch_snippets(bundle)
    write_snippets(rv, open("tm_" + bundle.lower() + ".snippets","w"))

