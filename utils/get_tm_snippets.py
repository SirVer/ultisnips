#!/usr/bin/env python
# encoding: utf-8

import urllib
import re
from xml.etree import ElementTree

def parse_content(c):
    data = ElementTree.fromstring(c)[0]

    rv = {}
    for k,v in zip(data[::2], data[1::2]):
        rv[k.text] = v.text

    return rv

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

        name = name.rsplit('.', 1)[0] # remove Extension
        print "Fetching data for Snippet '%s'" % name
        content = urllib.urlopen(snippet_idx + link).read()

        rv.append((name, parse_content(content)))

    return rv


def write_snippets(snip_descr, f):

    for name, d in snip_descr:
        if "tabTrigger" not in d:
            continue

        f.write('snippet %s "%s"\n' % (d["tabTrigger"], name))
        f.write(d["content"] + "\n")
        f.write("endsnippet\n\n")



if __name__ == '__main__':
    import sys

    bundle = sys.argv[1]
    rv = fetch_snippets(bundle)
    write_snippets(rv, open("tm_" + bundle.lower() + ".snippets","w"))

