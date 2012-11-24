#!/usr/bin/env python
# encoding: utf-8
"""
Convert snipmate compatible snippets to UltiSnips compatible snippets
by Phillip Berndt
"""
import sys
import re
import os
import argparse

def convert_snippet_contents(content):
    " If the snippet contains snipmate style substitutions, convert them to ultisnips style "
    content = re.sub("`([^`]+`)", "`!v \g<1>", content)
    return content

def convert_snippet_file(source):
    " One file per filetype "
    retval = ""
    state = 0
    for line in open(source).readlines():
        # Ignore empty lines
        if line.strip() == "":
            continue
        # The rest of the handling is stateful
        if state == 0:
            # Find snippet start. Keep comments.
            if line[:8] == "snippet ":
                snippet_info = re.match("(\S+)\s*(.*)", line[8:])
                if not snippet_info:
                    print >> sys.stderr, "Warning: Malformed snippet\n %s\n" % line
                    continue
                retval += 'snippet %s "%s"' % (snippet_info.group(1), snippet_info.group(2) if snippet_info.group(2) else snippet_info.group(1)) + "\n"
                state = 1
                snippet = ""
            elif line[:1] == "#":
                retval += line
                state = 0
        elif state == 1:
            # First line of snippet: Get indentation
            whitespace = re.search("^\s+", line)
            if not whitespace:
                print >> sys.stderr, "Warning: Malformed snippet, content not indented.\n"
                retval += "endsnippet\n\n"
                state = 0
            else:
                whitespace = whitespace.group(0)
                snippet += line[len(whitespace):]
                state = 2
        elif state == 2:
            # In snippet: If indentation level is the same, add to snippet. Else end snippet.
            if line[:len(whitespace)] == whitespace:
                snippet += line[len(whitespace):]
            else:
                retval += convert_snippet_contents(snippet) + "endsnippet\n\n"
                #Copy-paste the section from state=0 so that we don't skip every other snippet
                if line[:8] == "snippet ":
                    snippet_info = re.match("(\S+)\s*(.*)", line[8:])
                    if not snippet_info:
                        print >> sys.stderr, "Warning: Malformed snippet\n %s\n" % line
                        continue
                    retval += 'snippet %s "%s"' % (snippet_info.group(1), snippet_info.group(2) if snippet_info.group(2) else snippet_info.group(1)) + "\n"
                    state = 1
                    snippet = ""
                elif line[:1] == "#":
                    retval += line
                    state = 0
    if state == 2:
        retval += convert_snippet_contents(snippet) + "endsnippet\n\n"
    return retval

def convert_snippet(source):
    " One file per snippet "
    name = os.path.basename(source)[:-8]
    return 'snippet %s "%s"' % (name, name) + "\n" + \
        convert_snippet_contents(open(source).read()) + \
        "\nendsnippet\n"

def convert_snippets(source):
    if os.path.isdir(source):
        return "\n".join((convert_snippet(os.path.join(source, x)) for x in os.listdir(source) if x[-8:] == ".snippet"))
    else:
        return convert_snippet_file(source)

if __name__ == '__main__':
    # Parse command line
    argsp = argparse.ArgumentParser(description="Convert snipmate compatible snippets to UltiSnips' file format",
        epilog="example:\n  %s drupal/ drupal.snippets\n   will convert all drupal specific snippets from snipmate into one file drupal.snippets" % sys.argv[0],
        formatter_class=argparse.RawDescriptionHelpFormatter)
    argsp.add_argument("source", help="Source directory for one filetype or a snippets file")
    argsp.add_argument("target", help="File to write the resulting snippets into. If omitted, the snippets will be written to stdout.", nargs="?", default="-")
    args = argsp.parse_args()

    source_file_name = args.source
    tmp_file_name = ''.join([args.target,'.tmp'])
    try:
        tmp = sys.stdout if args.target == "-" else open(tmp_file_name, "w")
    except IOError:
        print >> sys.stderr, "Error: Failed to open output file %s for writing" % tmp_file_name
        sys.exit(1)

    snippets = convert_snippets(source_file_name)
    print >> tmp, snippets

    if args.target != "-":
        if os.access(args.target, os.F_OK):
            os.remove(args.target)
        os.rename(tmp_file_name, args.target)
