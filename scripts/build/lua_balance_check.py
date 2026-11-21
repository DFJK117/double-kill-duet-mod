# -*- coding: utf-8 -*-
"""粗略 Lua 块平衡检查：剥离字符串/注释后按 token 计数 function/if/for/while vs end。"""
import re, sys

def strip(code):
    out = []
    i = 0
    q = None
    while i < len(code):
        c = code[i]
        if q:
            if c == '\\':
                i += 2
                continue
            if c == q:
                q = None
            out.append(' ')
            i += 1
            continue
        if c in ('"', "'"):
            q = c
            out.append(' ')
            i += 1
            continue
        if c == '-' and i + 1 < len(code) and code[i + 1] == '-':
            break
        out.append(c)
        i += 1
    return ''.join(out)

def check(path):
    lines = open(path, encoding='utf-8').read().split('\n')
    depth = 0
    for ln, line in enumerate(lines, 1):
        c = strip(line)
        opens = len(re.findall(r'\bfunction\b', c))
        # 负向后顾已排除 elseif 中的 if，无需再单独减去 elseif
        opens += len(re.findall(r'(?<![\w])if\b', c))
        opens += len(re.findall(r'\bfor\b', c))
        opens += len(re.findall(r'\bwhile\b', c))
        # standalone do (not part of for/while already counted) - skip, rare here
        ends = len(re.findall(r'(?<![\w])end\b', c))
        depth += opens - ends
        if depth < 0:
            print('NEG depth at line %d: %r' % (ln, line))
            return False
    print('%s: final depth=%d (%s)' % (path, depth, 'BALANCED' if depth == 0 else 'UNBALANCED'))
    return depth == 0

if __name__ == '__main__':
    ok = True
    for p in sys.argv[1:]:
        ok = check(p) and ok
    sys.exit(0 if ok else 1)
