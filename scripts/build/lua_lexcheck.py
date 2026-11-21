# -*- coding: utf-8 -*-
"""Lua 5.1 lexical shape checker: strips comments/strings, verifies block balance.
Validated against a known-bad input (fullwidth dash breaking a long comment)."""
import sys, re


def strip_lua(src):
    """Return code with comments and string contents blanked, same length-ish.
    Handles: --[[ ]] long comments (incl [=[ levels), -- line comments,
    single/double quoted strings with escapes, and long strings [[ ]]."""
    out = []
    i = 0
    n = len(src)
    while i < n:
        c = src[i]
        # long comment --[=*[
        if c == '-' and i + 1 < n and src[i + 1] == '-':
            j = i + 2
            lvl = 0
            while j < n and src[j] == '=':
                lvl += 1
                j += 1
            if j < n and src[j] == '[':
                close = ']' + '=' * lvl + ']'
                k = src.find(close, j + 1)
                if k == -1:
                    raise SyntaxError('unterminated long comment at %d' % i)
                out.append(' ' * (k + len(close) - i))
                i = k + len(close)
                continue
            # line comment
            k = src.find('\n', i)
            if k == -1:
                k = n
            out.append(' ' * (k - i))
            i = k
            continue
        # long string [=*[
        if c == '[':
            j = i + 1
            lvl = 0
            while j < n and src[j] == '=':
                lvl += 1
                j += 1
            if j < n and src[j] == '[':
                close = ']' + '=' * lvl + ']'
                k = src.find(close, j + 1)
                if k == -1:
                    raise SyntaxError('unterminated long string at %d' % i)
                out.append(' ' * (k + len(close) - i))
                i = k + len(close)
                continue
        # quoted strings
        if c in ('"', "'"):
            q = c
            j = i + 1
            while j < n:
                if src[j] == '\\':
                    j += 2
                    continue
                if src[j] == q:
                    j += 1
                    break
                j += 1
            out.append(' ' * (j - i))
            i = j
            continue
        out.append(c)
        i += 1
    return ''.join(out)


def check(path):
    src = open(path, encoding='utf-8').read()
    # 1) no non-ascii anywhere (project rule for this script)
    bad = [(i, ord(ch)) for i, ch in enumerate(src) if ord(ch) > 127]
    code = strip_lua(src)
    lines = code.split('\n')

    opens = 0
    stack = []
    # tokens that open a block: function/if/for/while/do (standalone) ; repeat
    # closers: end (closes function/if/for/while/do), until (closes repeat)
    for ln, line in enumerate(lines, 1):
        # count do that is NOT part of "for ... do"/"while ... do" and not "do" after then
        toks = re.findall(r"[A-Za-z_]\w*|\S", line)
        # simple word scan (strings/comments already blanked)
        words = re.findall(r"\b(function|if|for|while|do|repeat|end|until|then|elseif|else)\b", line)
        # walk words maintaining mini-state to catch standalone do
        for w in words:
            if w in ('function', 'if', 'for', 'while', 'repeat'):
                stack.append((w, ln))
            elif w == 'do':
                # 'do' opens only if it's a standalone block (not the do of for/while).
                # Heuristic: previous word on line is 'then' or line starts with do
                prev = None
                idx = line.find('do')
                # find previous word before this do
                before = line[:idx]
                pw = re.findall(r"\b(\w+)\b", before)
                prev = pw[-1] if pw else None
                if prev in ('for', 'while') or re.search(r"\b(for|while)\b[^\n]*$", before) and prev not in ('then',):
                    # belongs to for/while, skip (already counted)
                    pass
                else:
                    stack.append((w, ln))
            elif w == 'end':
                if stack:
                    stack.pop()
                else:
                    print('EXTRA end at line', ln)
            elif w == 'until':
                if stack and stack[-1][0] == 'repeat':
                    stack.pop()
                else:
                    print('ORPHAN until at line', ln)

    ok = not bad and not stack
    print('FILE', path)
    print('  non-ascii chars:', len(bad), bad[:5])
    print('  unclosed blocks:', stack[:10])
    print('  RESULT:', 'OK' if ok else 'FAIL')
    return ok


if __name__ == '__main__':
    for p in sys.argv[1:]:
        check(p)
