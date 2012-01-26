#!/usr/bin/env python
# encoding: utf-8

from collections import defaultdict
import sys

def matches(initial_line, a, b, cmds):
    buf = a[:]
    for cmd in cmds:
        ctype, line, col, char = cmd
        line -= initial_line
        if ctype == "D":
            if char != '\n':
                buf[line] = buf[line][:col] + buf[line][col+len(char):]
            else:
                buf[line] = buf[line] + buf[line+1]
                del buf[line+1]
        elif ctype == "I":
            buf[line] = buf[line][:col] + char + buf[line][col:]
        buf = '\n'.join(buf).split('\n')
    return len(buf) == len(b) and all(j==k for j,k in zip(buf, b))

# TODO: module name only makes limited sense by now
def guess_edit(initial_line, lt, ct, ppos, pos): # TODO: maybe guess edit from movement?
    if not len(lt) and not len(ct): return True, ()
    if pos.line == ppos.line: # Movement only in one line
        llen = len(lt[ppos.line - initial_line])
        clen = len(ct[pos.line - initial_line])
        if ppos < pos and clen > llen: # Likely that only characters have been added
            es = (
                ("I", ppos.line, ppos.col, ct[ppos.line - initial_line][ppos.col:pos.col]),
            )
            if matches(initial_line, lt, ct, es): return True, es
        if clen < llen:
            if ppos == pos: # 'x' or DEL or dt or something
                es = (
                    ("D", pos.line, pos.col, lt[ppos.line - initial_line][ppos.col:ppos.col + (llen - clen)]),
                )
                if matches(initial_line, lt, ct, es): return True, es
            if pos < ppos: # Backspacing or dT dF?
                es = (
                    ("D", pos.line, pos.col, lt[pos.line - initial_line][pos.col:pos.col + llen - clen]),
                )
                if matches(initial_line, lt, ct, es): return True, es
    return False, None

def edit_script(a, b, sline = 0):
    """
    Return a list of deletions and insertions that will turn a into b. This is
    done by traversing an implicit edit graph and searching for the shortest
    route. The basic idea is as follows:

        - Matching a character is free as long as there was no deletion/insertion
          before. Then, matching will be seen as delete + insert [1].
        - Deleting one character has the same cost everywhere. Each additional
          character costs only have of the first deletion.
        - Insertion is cheaper the earlier it happes. The first character is more
          expensive that any later [2].

    [1] This is that world -> aolsa will be "D" world + "I" aolsa instead of
        "D" w , "D" rld, "I" a, "I" lsa
    [2] This is that "hello\n\n" -> "hello\n\n\n" will insert a newline after hello
        and not after \n
    """
    d = defaultdict(list)
    seen = defaultdict(lambda: sys.maxint)

    d[0] = [ (0,0,sline, 0, ()) ]

    cost = 0
    D_COST = len(a)+len(b)
    I_COST = len(a)+len(b)
    while True:
        while len(d[cost]):
            x, y, line, col, what = d[cost].pop()

            if a[x:] == b[y:]:
                return what

            if x < len(a) and y < len(b) and a[x] == b[y]:
                ncol = col + 1
                nline = line
                if a[x] == '\n':
                    ncol = 0
                    nline +=1
                lcost = cost + 1
                if (what and what[-1][0] == "D" and what[-1][1] == line and
                        what[-1][2] == col and a[x] != '\n'):
                    # Matching directly after a deletion should be as costly as
                    # DELETE + INSERT + a bit
                    lcost = (D_COST + I_COST)*1.5
                if seen[x+1,y+1] > lcost:
                    d[lcost].append((x+1,y+1, nline, ncol, what))
                    seen[x+1,y+1] = lcost

            if y < len(b): # INSERT
                ncol = col + 1
                nline = line
                if b[y] == '\n':
                    ncol = 0
                    nline += 1
                if (what and what[-1][0] == "I" and what[-1][1] == nline and
                    what[-1][2]+len(what[-1][-1]) == col and b[y] != '\n' and
                    seen[x,y+1] > cost + (I_COST + ncol) // 2
                ):
                    seen[x,y+1] = cost + (I_COST + ncol) // 2
                    d[cost + (I_COST + ncol) // 2].append(
                        (x,y+1, line, ncol, what[:-1] + (
                            ("I", what[-1][1], what[-1][2], what[-1][-1] + b[y]),) )
                    )
                elif seen[x,y+1] > cost + I_COST + ncol:
                    seen[x,y+1] = cost + I_COST + ncol
                    d[cost + ncol + I_COST].append((x,y+1, nline, ncol,
                        what + (("I", line, col,b[y]),))
                    )
            if x < len(a): # DELETE
                if (what and what[-1][0] == "D" and what[-1][1] == line and
                    what[-1][2] == col and a[x] != '\n' and what[-1][-1] != '\n' and
                    seen[x+1,y] > cost + D_COST // 2
                ):
                    seen[x+1,y] = cost + D_COST // 2
                    d[cost + D_COST // 2].append((x+1,y, line, col, what[:-1] +
                        (("D",line, col, what[-1][-1] + a[x]),) )
                    )
                elif seen[x+1,y] > cost + D_COST:
                    seen[x+1,y] = cost + D_COST
                    d[cost + D_COST].append((x+1,y, line, col, what +
                        (("D",line, col, a[x]),) )
                    )
        cost += 1

