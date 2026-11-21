# -*- coding: utf-8 -*-
import os, zipfile, hashlib
A = r'E:\UGUSDTIOUIYSRGIUUHSRGIH\Downloads\vs-impostor-legacy-1.1.2\VS IMPOSTOR LEGACY 1.1.2\assets'
targets = []
def want(rel):
    r = rel.replace('\\', '/')
    return (r.startswith('songs/double-kill-duo-') or
            r.startswith('data/stages/cargo-duo-') or
            r.startswith('data/weeks/dk-duo-') or
            r.startswith('images/icons/icon-momo') or
            r.startswith('images/icons/icon-miku') or
            r.startswith('images/icons/icon-teto') or
            '/characters/momo' in r or '/characters/miku' in r or '/characters/teto' in r or
            r.startswith('images/menucharacters') or
            r.startswith('images/storymenu/dk-') or
            r.startswith('images/menudifficulties'))
for sub in ['songs', 'data', 'images']:
    base = os.path.join(A, sub)
    for root, _, fs in os.walk(base):
        for f in fs:
            p = os.path.join(root, f)
            rel = os.path.relpath(p, A)
            if want(rel):
                targets.append((p, 'assets/' + rel.replace('\\', '/')))
for c in ['momo','miku','teto','momo-god','miku-god','teto-god','bf-ic','bf-god','bf-defeat-normal','bf-defeat-normal-god']:
    p = os.path.join(A, 'data', 'characters', c + '.json')
    if os.path.isfile(p):
        arc = 'assets/data/characters/' + c + '.json'
        if all(a != arc for _, a in targets):
            targets.append((p, arc))
out = r'E:\UST_work\DK_Duet_遗产版_assets直装_20261121.zip'
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for p, arc in targets:
        z.write(p, arc)
raw = sum(os.path.getsize(p) for p, _ in targets)
print('files=', len(targets), 'raw=', round(raw/1024/1024, 1), 'MB')
print('zip=', round(os.path.getsize(out)/1024/1024, 1), 'MB', 'md5=', hashlib.md5(open(out,'rb').read()).hexdigest())
z = zipfile.ZipFile(out)
print('CRC=', 'OK' if z.testzip() is None else 'BAD')
