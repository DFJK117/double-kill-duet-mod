# -*- coding: utf-8 -*-
import re, zipfile, hashlib

files = {
    'DK_Miku': r'E:/UST_work/dk_miku/DK_Miku/scripts/BOTPLAY_Pro.lua',
    'DK_Dual': r'E:/UST_work/dk_miku/DK_Dual/scripts/BOTPLAY_Pro.lua',
    'game':    r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet/scripts/BOTPLAY_Pro.lua',
}
def md5b(b): return hashlib.md5(b).hexdigest()
def md5(p):  return md5b(open(p, 'rb').read())

def strip_code(t):
    t = re.sub(r'--\[\[.*?\]\]', '', t, flags=re.S)
    t = re.sub(r'--[^\n]*', '', t)
    # 单引号字符串
    t = re.sub(r"'(?:[^'\\]|\\.)*'", 'S', t)
    # 双引号字符串
    t = re.sub(r'"(?:[^"\\]|\\.)*"', 'S', t)
    return t

for k, p in files.items():
    raw = open(p, encoding='utf-8').read()
    c = strip_code(raw)
    nfun  = len(re.findall(r'\bfunction\b', c))
    nif   = len(re.findall(r'\bif\b', c))
    nfor  = len(re.findall(r'\bfor\b', c))
    nwhile= len(re.findall(r'\bwhile\b', c))
    nend  = len(re.findall(r'\bend\b', c))
    # function/if/for/while 各占一个 end（Lua 里 repeat 用 until，这里没有 repeat）
    need = nfun + nif + nfor + nwhile
    print('%-8s md5=%s lines=%d blocks(need=%d end=%d) %s'
          % (k, md5(p), len(raw.splitlines()), need, nend,
             'OK' if need == nend else 'MISMATCH'))

z = zipfile.ZipFile(r'E:/UST_work/dk_miku/DK_Duet_FULL_v11.33_BPPIndependent_20261119.zip')
data = z.read('DK_Duet/scripts/BOTPLAY_Pro.lua')
print('ZIP inner md5', md5b(data), '== game', md5b(data) == md5(files['game']))
